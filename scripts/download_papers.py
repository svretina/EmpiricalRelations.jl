#!/usr/bin/env python3
"""Reproducibly acquire and safely extract an arXiv literature collection."""

from __future__ import annotations

import argparse
import email.utils
import gzip
import hashlib
import json
import os
import re
import shutil
import tarfile
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO, Callable


ARXIV_ID_RE = re.compile(
    r"^(?:\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?$",
    re.IGNORECASE,
)
VERSION_RE = re.compile(r"v(\d+)$")
YEAR_RE = re.compile(r"(?<!\d)(19\d{2}|20\d{2})(?!\d)")
FIGURE_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".eps", ".ps", ".svg"}
ATOM = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
MAX_SOURCE_BYTES = 100 * 1024 * 1024
MAX_EXTRACTED_BYTES = 500 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 20_000
DEFAULT_USER_AGENT = "EmpiricalRelations.jl literature collector (contact: svretina@gmail.com)"


class AcquisitionError(RuntimeError):
    pass


class UnsafeArchiveError(AcquisitionError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def validate_arxiv_id(value: str) -> str:
    value = value.strip()
    if not ARXIV_ID_RE.fullmatch(value):
        raise ValueError(f"invalid arXiv identifier: {value!r}")
    return value


def base_arxiv_id(value: str) -> str:
    return VERSION_RE.sub("", validate_arxiv_id(value))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def valid_pdf(path: Path) -> bool:
    try:
        with path.open("rb") as stream:
            return stream.read(8).lstrip().startswith(b"%PDF-")
    except OSError:
        return False


def ascii_slug(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", value.lower()) or "unknown"


def first_author_slug(authors: list[str]) -> str:
    if not authors:
        return "unknown"
    name = re.sub(r"\s+", " ", authors[0].strip())
    if "," in name:
        surname = name.split(",", 1)[0]
    else:
        surname = name.split()[-1]
    return ascii_slug(surname)


def publication_year(metadata: dict[str, Any]) -> int:
    if metadata.get("publication_year"):
        return int(metadata["publication_year"])
    journal_ref = metadata.get("journal_reference") or ""
    years = [int(match) for match in YEAR_RE.findall(journal_ref)]
    if years:
        return years[-1]
    return int(metadata["submitted"][:4])


def directory_name(metadata: dict[str, Any]) -> str:
    return f"{base_arxiv_id(metadata['arxiv_id']).replace('/', '_')}_{first_author_slug(metadata['authors'])}_{publication_year(metadata)}"


def load_seeds(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = raw.get("papers", raw) if isinstance(raw, dict) else raw
    if not isinstance(records, list):
        raise ValueError("seed file must contain a list or a 'papers' list")
    merged: dict[str, dict[str, Any]] = {}
    for item in records:
        if not isinstance(item, dict) or "arxiv_id" not in item:
            raise ValueError("each seed must be an object with arxiv_id")
        arxiv_id = base_arxiv_id(str(item["arxiv_id"]))
        if arxiv_id not in merged:
            merged[arxiv_id] = {**item, "arxiv_id": arxiv_id}
            merged[arxiv_id]["topics"] = list(dict.fromkeys(item.get("topics", [])))
        else:
            merged[arxiv_id]["topics"] = list(
                dict.fromkeys(merged[arxiv_id].get("topics", []) + item.get("topics", []))
            )
    return list(merged.values())


class RateLimiter:
    def __init__(self, interval: float = 3.0, clock: Callable[[], float] = time.monotonic,
                 sleeper: Callable[[float], None] = time.sleep):
        self.interval = max(0.0, interval)
        self.clock = clock
        self.sleeper = sleeper
        self.last_request: float | None = None

    def wait(self) -> None:
        if self.last_request is not None:
            remaining = self.interval - (self.clock() - self.last_request)
            if remaining > 0:
                self.sleeper(remaining)
        self.last_request = self.clock()


class HttpClient:
    def __init__(self, user_agent: str = DEFAULT_USER_AGENT, interval: float = 3.0,
                 retries: int = 4, timeout: float = 60.0,
                 opener: Callable[..., Any] = urllib.request.urlopen,
                 sleeper: Callable[[float], None] = time.sleep):
        self.user_agent = user_agent
        self.retries = retries
        self.timeout = timeout
        self.opener = opener
        self.sleeper = sleeper
        self.limiter = RateLimiter(interval=interval, sleeper=sleeper)

    def open(self, url: str):
        transient = {408, 425, 429, 500, 502, 503, 504}
        for attempt in range(self.retries + 1):
            self.limiter.wait()
            request = urllib.request.Request(
                url,
                headers={"User-Agent": self.user_agent, "Accept-Encoding": "identity"},
            )
            try:
                return self.opener(request, timeout=self.timeout)
            except urllib.error.HTTPError as error:
                if error.code not in transient or attempt >= self.retries:
                    raise
                retry_after = error.headers.get("Retry-After")
                delay = parse_retry_after(retry_after) if retry_after else 2 ** attempt
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                if attempt >= self.retries:
                    raise
                delay = 2 ** attempt
            self.sleeper(min(max(delay, 0.0), 120.0))
        raise AssertionError("retry loop exhausted")

    def read(self, url: str, limit: int = MAX_SOURCE_BYTES) -> tuple[bytes, str, str]:
        with self.open(url) as response:
            data = read_limited(response, limit)
            content_type = response.headers.get_content_type()
            final_url = response.geturl()
        return data, content_type, final_url

    def download(self, url: str, destination: Path, limit: int) -> tuple[str, str, int]:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.name + ".part")
        digest = hashlib.sha256()
        size = 0
        try:
            with self.open(url) as response, temporary.open("wb") as output:
                final_url = response.geturl()
                content_type = response.headers.get_content_type()
                while chunk := response.read(1024 * 1024):
                    size += len(chunk)
                    if size > limit:
                        raise AcquisitionError(f"response exceeds {limit} bytes")
                    digest.update(chunk)
                    output.write(chunk)
                output.flush()
                os.fsync(output.fileno())
            temporary.replace(destination)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
        return final_url, content_type, size


def parse_retry_after(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        parsed = email.utils.parsedate_to_datetime(value)
        return max(0.0, (parsed - datetime.now(parsed.tzinfo)).total_seconds())


def read_limited(stream: BinaryIO, limit: int) -> bytes:
    result = bytearray()
    while chunk := stream.read(min(1024 * 1024, limit + 1 - len(result))):
        result.extend(chunk)
        if len(result) > limit:
            raise AcquisitionError(f"response exceeds {limit} bytes")
    return bytes(result)


def parse_atom(payload: bytes) -> dict[str, dict[str, Any]]:
    root = ET.fromstring(payload)
    output: dict[str, dict[str, Any]] = {}
    for entry in root.findall("a:entry", ATOM):
        identity = (entry.findtext("a:id", default="", namespaces=ATOM).rstrip("/").split("/")[-1])
        if not identity or entry.find("a:title", ATOM) is None:
            continue
        arxiv_id = base_arxiv_id(identity)
        links = {link.attrib.get("rel", "alternate"): link.attrib.get("href") for link in entry.findall("a:link", ATOM)}
        authors = [node.findtext("a:name", default="", namespaces=ATOM).strip() for node in entry.findall("a:author", ATOM)]
        categories = [node.attrib["term"] for node in entry.findall("a:category", ATOM) if "term" in node.attrib]
        doi = entry.findtext("arxiv:doi", default=None, namespaces=ATOM)
        journal_ref = entry.findtext("arxiv:journal_ref", default=None, namespaces=ATOM)
        primary = entry.find("arxiv:primary_category", ATOM)
        output[arxiv_id] = {
            "arxiv_id": arxiv_id,
            "resolved_version": identity,
            "version": int(VERSION_RE.search(identity).group(1)) if VERSION_RE.search(identity) else None,
            "title": clean_space(entry.findtext("a:title", default="", namespaces=ATOM)),
            "authors": authors,
            "abstract": clean_space(entry.findtext("a:summary", default="", namespaces=ATOM)),
            "submitted": entry.findtext("a:published", default="", namespaces=ATOM),
            "last_revised": entry.findtext("a:updated", default="", namespaces=ATOM),
            "doi": doi,
            "journal_reference": journal_ref,
            "arxiv_categories": categories,
            "primary_category": primary.attrib.get("term") if primary is not None else None,
            "abstract_url": links.get("alternate", f"https://arxiv.org/abs/{identity}"),
            "pdf_url": f"https://export.arxiv.org/pdf/{identity}",
            "source_url": f"https://export.arxiv.org/src/{identity}",
        }
    return output


def clean_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def fetch_metadata(client: HttpClient, identifiers: list[str]) -> dict[str, dict[str, Any]]:
    query = ",".join(identifiers)
    url = f"https://export.arxiv.org/api/query?id_list={query}&max_results={len(identifiers)}"
    payload, content_type, _ = client.read(url, limit=10 * 1024 * 1024)
    if "xml" not in content_type and not payload.lstrip().startswith(b"<?xml"):
        raise AcquisitionError(f"arXiv metadata endpoint returned {content_type}")
    return parse_atom(payload)


def crossref_publication(client: HttpClient, doi: str) -> dict[str, Any]:
    encoded = urllib.parse.quote(doi, safe="")
    payload, content_type, _ = client.read(f"https://api.crossref.org/works/{encoded}", limit=5 * 1024 * 1024)
    if "json" not in content_type and not payload.lstrip().startswith(b"{"):
        raise AcquisitionError(f"Crossref returned {content_type} for {doi}")
    message = json.loads(payload)["message"]
    selected = None
    selected_kind = None
    for kind in ("published-print", "published-online", "published", "issued"):
        parts = message.get(kind, {}).get("date-parts", [])
        if parts and parts[0]:
            selected = parts[0]
            selected_kind = kind
            break
    if not selected:
        return {"publication_date": None, "publication_date_source": None}
    date = "-".join(f"{part:02d}" if index else str(part) for index, part in enumerate(selected))
    return {
        "publication_date": date,
        "publication_year": int(selected[0]),
        "publication_date_source": f"Crossref:{selected_kind}",
        "publisher": message.get("publisher"),
        "container_title": (message.get("container-title") or [None])[0],
    }


def enrich_publication_metadata(client: HttpClient, records: dict[str, dict[str, Any]], papers_dir: Path) -> None:
    """Add journal dates from Crossref, reusing previously persisted enrichment."""
    for arxiv_id, record in records.items():
        doi = record.get("doi")
        if not doi:
            record.update(publication_date=None, publication_year=publication_year(record), publication_date_source=None)
            continue
        prefix = base_arxiv_id(arxiv_id).replace("/", "_") + "_"
        cached = None
        for path in papers_dir.glob(prefix + "*/metadata.json"):
            try:
                candidate = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if candidate.get("doi") == doi and candidate.get("publication_date"):
                cached = {key: candidate.get(key) for key in (
                    "publication_date", "publication_year", "publication_date_source", "publisher", "container_title"
                )}
                break
        try:
            record.update(cached or crossref_publication(client, doi))
        except Exception as error:
            record.update(
                publication_date=None,
                publication_year=publication_year(record),
                publication_date_source=None,
                publication_metadata_error=str(error),
            )


def detect_source(path: Path, content_type: str = "") -> tuple[str, str]:
    head = path.read_bytes()[:4096]
    if head.startswith(b"%PDF-"):
        return "pdf", ".pdf"
    if head.startswith(b"PK\x03\x04"):
        return "zip", ".zip"
    if head.startswith(b"BZh"):
        return "bzip2", ".bz2"
    if head.startswith(b"\xfd7zXZ\x00"):
        return "xz", ".xz"
    if head.startswith(b"\x1f\x8b"):
        try:
            with gzip.open(path, "rb") as stream:
                decompressed = stream.read(4096)
            if len(decompressed) >= 262 and decompressed[257:262] == b"ustar":
                return "gzip_tar", ".tar.gz"
            if looks_like_tex(decompressed):
                return "gzip_tex", ".tex.gz"
        except (OSError, EOFError):
            pass
        return "gzip", ".gz"
    if tarfile.is_tarfile(path):
        return "tar", ".tar"
    if looks_like_tex(head):
        return "tex", ".tex"
    if looks_like_html(head) or "html" in content_type:
        return "html", ".html"
    return "binary", ".bin"


def looks_like_tex(data: bytes) -> bool:
    sample = data.decode("utf-8", "ignore")
    return any(token in sample for token in ("\\documentclass", "\\begin{document}", "\\input{", "\\def\\"))


def looks_like_html(data: bytes) -> bool:
    sample = data[:2048].lower().lstrip()
    return sample.startswith((b"<!doctype html", b"<html", b"<?xml")) or b"<html" in sample


def safe_member_path(root: Path, member_name: str) -> Path:
    normalized = member_name.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if pure.is_absolute() or ".." in pure.parts or not pure.parts:
        raise UnsafeArchiveError(f"unsafe archive path: {member_name!r}")
    target = root.joinpath(*pure.parts)
    root_resolved = root.resolve()
    if os.path.commonpath((root_resolved, target.resolve())) != str(root_resolved):
        raise UnsafeArchiveError(f"archive path escapes extraction root: {member_name!r}")
    return target


def copy_limited(source: BinaryIO, destination: BinaryIO, budget: list[int]) -> None:
    while chunk := source.read(1024 * 1024):
        budget[0] += len(chunk)
        if budget[0] > MAX_EXTRACTED_BYTES:
            raise UnsafeArchiveError("archive exceeds decompressed size limit")
        destination.write(chunk)


def extract_tar(path: Path, destination: Path) -> None:
    budget = [0]
    with tarfile.open(path, "r:*") as archive:
        members = archive.getmembers()
        if len(members) > MAX_ARCHIVE_MEMBERS:
            raise UnsafeArchiveError("archive has too many members")
        for member in members:
            target = safe_member_path(destination, member.name)
            if member.issym() or member.islnk():
                raise UnsafeArchiveError(f"links are not allowed: {member.name!r}")
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                extracted = archive.extractfile(member)
                if extracted is None:
                    raise UnsafeArchiveError(f"cannot read archive member: {member.name!r}")
                with extracted, target.open("wb") as output:
                    copy_limited(extracted, output, budget)


def extract_zip(path: Path, destination: Path) -> None:
    budget = [0]
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        if len(members) > MAX_ARCHIVE_MEMBERS:
            raise UnsafeArchiveError("archive has too many members")
        for member in members:
            target = safe_member_path(destination, member.filename)
            if (member.external_attr >> 16) & 0o170000 == 0o120000:
                raise UnsafeArchiveError(f"symlinks are not allowed: {member.filename!r}")
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, target.open("wb") as output:
                    copy_limited(source, output, budget)


def extract_source(path: Path, source_type: str, destination: Path) -> None:
    staging = destination.with_name(destination.name + ".extracting")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    try:
        if source_type in {"gzip_tar", "tar"}:
            extract_tar(path, staging)
        elif source_type == "zip":
            extract_zip(path, staging)
        elif source_type == "gzip_tex":
            with gzip.open(path, "rb") as source, (staging / "submission.tex").open("wb") as output:
                copy_limited(source, output, [0])
        elif source_type == "tex":
            shutil.copy2(path, staging / "submission.tex")
        else:
            raise AcquisitionError(f"source type {source_type!r} is not extractable")
        if destination.exists():
            shutil.rmtree(destination)
        staging.replace(destination)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def strip_tex_comments(text: str) -> str:
    return re.sub(r"(?<!\\)%.*", "", text)


def tex_root_candidates(source_dir: Path) -> list[dict[str, Any]]:
    tex_files = sorted(source_dir.rglob("*.tex"))
    included: set[Path] = set()
    details: list[dict[str, Any]] = []
    for path in tex_files:
        try:
            text = strip_tex_comments(path.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
        relative = path.relative_to(source_dir)
        has_class = bool(re.search(r"\\documentclass(?:\[[^]]*\])?\s*\{", text))
        has_document = "\\begin{document}" in text
        dependencies = []
        for match in re.finditer(r"\\(?:input|include)\s*\{([^}]+)\}", text):
            dependency = match.group(1).strip()
            dependency_path = (path.parent / dependency)
            if not dependency_path.suffix:
                dependency_path = dependency_path.with_suffix(".tex")
            try:
                included.add(dependency_path.resolve().relative_to(source_dir.resolve()))
                dependencies.append(str(dependency_path.resolve().relative_to(source_dir.resolve())))
            except ValueError:
                dependencies.append(dependency)
        score = 4 * has_class + 3 * has_document + (1 if relative.parent == Path(".") else 0)
        details.append({
            "path": relative.as_posix(),
            "has_documentclass": has_class,
            "has_begin_document": has_document,
            "dependencies": dependencies,
            "score": score,
        })
    for detail in details:
        if Path(detail["path"]) not in included:
            detail["score"] += 2
    candidates = [item for item in details if item["has_documentclass"] and item["has_begin_document"]]
    return sorted(candidates, key=lambda item: (-item["score"], item["path"]))


def inventory_source(source_dir: Path) -> dict[str, list[str]]:
    inventory = {"tex": [], "bibliography": [], "styles": [], "figures": [], "other": []}
    for path in sorted(item for item in source_dir.rglob("*") if item.is_file()):
        relative = path.relative_to(source_dir).as_posix()
        suffix = path.suffix.lower()
        if suffix == ".tex":
            inventory["tex"].append(relative)
        elif suffix == ".bib":
            inventory["bibliography"].append(relative)
        elif suffix in {".sty", ".cls", ".bst", ".bbx", ".cbx"}:
            inventory["styles"].append(relative)
        elif suffix in FIGURE_SUFFIXES:
            inventory["figures"].append(relative)
        else:
            inventory["other"].append(relative)
    return inventory


def json_write(path: Path, value: Any) -> None:
    temporary = path.with_name(path.name + ".part")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def existing_file_valid(path: Path, metadata: dict[str, Any], key: str, validator: Callable[[Path], bool] | None = None) -> bool:
    if not path.is_file() or (validator is not None and not validator(path)):
        return False
    expected = metadata.get("checksums", {}).get(key)
    return expected is None or expected == sha256_file(path)


def download_one(client: HttpClient, seed: dict[str, Any], arxiv: dict[str, Any], papers_dir: Path,
                 force: bool = False) -> dict[str, Any]:
    folder = papers_dir / directory_name(arxiv)
    prefix = base_arxiv_id(arxiv["arxiv_id"]).replace("/", "_") + "_"
    previous_folders = [path for path in papers_dir.glob(prefix + "*") if path.is_dir() and path != folder]
    if not folder.exists() and len(previous_folders) == 1:
        previous_folders[0].rename(folder)
    folder.mkdir(parents=True, exist_ok=True)
    metadata_path = folder / "metadata.json"
    old = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
    metadata = {
        **arxiv,
        "publication_year": publication_year(arxiv),
        "publication_date": arxiv.get("publication_date"),
        "publication_date_source": arxiv.get("publication_date_source"),
        "publisher": arxiv.get("publisher"),
        "container_title": arxiv.get("container_title"),
        "categories": seed.get("topics", []),
        "seed_group": seed.get("group"),
        "directory": folder.name,
        "accessed_at": utc_now(),
        "pdf_status": "pending",
        "source_status": "pending",
        "tex_status": "not_attempted",
        "main_tex": None,
        "main_tex_candidates": [],
        "source_response_type": None,
        "source_original_filename": None,
        "checksums": dict(old.get("checksums", {})),
        "errors": [],
    }
    # Preserve reviewed, paper-local semantic annotations across acquisition
    # refreshes. These fields are curated independently of arXiv metadata.
    if "frequency_nomenclature" in old:
        metadata["frequency_nomenclature"] = old["frequency_nomenclature"]

    pdf_path = folder / "paper.pdf"
    try:
        if force or not existing_file_valid(pdf_path, old, "pdf_sha256", valid_pdf):
            final_url, content_type, size = client.download(arxiv["pdf_url"], pdf_path, 100 * 1024 * 1024)
            if not valid_pdf(pdf_path):
                pdf_path.unlink(missing_ok=True)
                raise AcquisitionError(f"PDF endpoint returned invalid content ({content_type})")
        else:
            final_url, size = old.get("pdf_final_url", arxiv["pdf_url"]), pdf_path.stat().st_size
        metadata.update(pdf_status="downloaded", pdf_final_url=final_url, pdf_bytes=size)
        metadata["checksums"]["pdf_sha256"] = sha256_file(pdf_path)
    except Exception as error:
        metadata["pdf_status"] = "failed"
        metadata["errors"].append({"stage": "pdf", "message": str(error)})

    old_source_name = old.get("source_original_filename")
    source_path = folder / old_source_name if old_source_name else None
    try:
        if force or source_path is None or not existing_file_valid(source_path, old, "source_sha256"):
            temporary_source = folder / "source.download"
            final_url, content_type, size = client.download(arxiv["source_url"], temporary_source, MAX_SOURCE_BYTES)
            source_type, extension = detect_source(temporary_source, content_type)
            if source_type == "html":
                temporary_source.unlink(missing_ok=True)
                raise AcquisitionError("source endpoint returned HTML instead of submission source")
            source_path = folder / f"source{extension}"
            if source_path.exists() and source_path != temporary_source:
                source_path.unlink()
            temporary_source.replace(source_path)
        else:
            source_type, _ = detect_source(source_path)
            final_url, content_type, size = old.get("source_final_url", arxiv["source_url"]), old.get("source_content_type"), source_path.stat().st_size
        metadata.update(
            source_status="downloaded",
            source_response_type=source_type,
            source_original_filename=source_path.name,
            source_final_url=final_url,
            source_content_type=content_type,
            source_bytes=size,
        )
        metadata["checksums"]["source_sha256"] = sha256_file(source_path)

        if source_type in {"gzip_tar", "tar", "zip", "gzip_tex", "tex"}:
            source_dir = folder / "source"
            if force or not source_dir.exists() or old.get("checksums", {}).get("source_sha256") != metadata["checksums"]["source_sha256"]:
                extract_source(source_path, source_type, source_dir)
            inventory = inventory_source(source_dir)
            candidates = tex_root_candidates(source_dir)
            metadata["source_inventory"] = inventory
            metadata["main_tex_candidates"] = candidates
            metadata["tex_status"] = "extracted" if inventory["tex"] else "no_tex_found"
            if candidates:
                best_score = candidates[0]["score"]
                best = [item for item in candidates if item["score"] == best_score]
                metadata["main_tex"] = f"source/{best[0]['path']}"
                metadata["main_tex_ambiguous"] = len(best) > 1
                shutil.copy2(source_dir / best[0]["path"], folder / "main.tex")
            else:
                metadata["main_tex_ambiguous"] = False
        else:
            metadata["tex_status"] = "not_tex"
    except urllib.error.HTTPError as error:
        metadata["source_status"] = "unavailable" if error.code in {400, 404} else "failed"
        metadata["tex_status"] = "unavailable"
        metadata["errors"].append({"stage": "source", "message": f"HTTP {error.code}: {error.reason}"})
    except Exception as error:
        metadata["source_status"] = "failed"
        metadata["tex_status"] = "failed"
        metadata["errors"].append({"stage": "source", "message": str(error)})

    json_write(metadata_path, metadata)
    return metadata


def bibtex_key(metadata: dict[str, Any]) -> str:
    return f"{first_author_slug(metadata.get('authors', []))}{metadata.get('publication_year', 'unknown')}{base_arxiv_id(metadata['arxiv_id']).replace('.', '')}"


def bibtex_escape(value: str) -> str:
    return value.replace("\\", "\\textbackslash ").replace("{", "\\{").replace("}", "\\}")


def write_catalogues(papers_dir: Path, seeds: list[dict[str, Any]], records: list[dict[str, Any]]) -> None:
    indexed = {item["arxiv_id"]: item for item in records}
    entries = [indexed.get(seed["arxiv_id"], {
        "arxiv_id": seed["arxiv_id"], "categories": seed.get("topics", []),
        "seed_group": seed.get("group"), "pdf_status": "not_attempted",
        "source_status": "not_attempted", "tex_status": "not_attempted",
        "errors": [{"stage": "metadata", "message": "metadata unavailable"}],
    }) for seed in seeds]
    summary = {
        "total": len(entries),
        "pdfs_downloaded": sum(item.get("pdf_status") == "downloaded" for item in entries),
        "sources_downloaded": sum(item.get("source_status") == "downloaded" for item in entries),
        "tex_projects_extracted": sum(item.get("tex_status") == "extracted" for item in entries),
        "sources_unavailable": sum(item.get("source_status") == "unavailable" for item in entries),
        "failed": sum(bool(item.get("errors")) for item in entries),
        "ambiguous_roots": sum(bool(item.get("main_tex_ambiguous")) for item in entries),
    }
    manifest = {"schema_version": 1, "generated_at": utc_now(), "summary": summary, "papers": entries}
    json_write(papers_dir / "manifest.json", manifest)

    lines = ["% Generated by scripts/download_papers.py; edit seeds.json, not this file.", ""]
    for item in entries:
        if not item.get("title"):
            continue
        fields = {
            "title": item["title"],
            "author": " and ".join(item.get("authors", [])),
            "year": str(item.get("publication_year", "")),
            "eprint": item["arxiv_id"],
            "archivePrefix": "arXiv",
            "primaryClass": item.get("primary_category") or "",
            "doi": item.get("doi") or "",
            "url": item.get("abstract_url") or "",
        }
        lines.append(f"@article{{{bibtex_key(item)},")
        for key, value in fields.items():
            if value:
                lines.append(f"  {key} = {{{bibtex_escape(value)}}},")
        lines.extend(["}", ""])
    (papers_dir / "bibliography.bib").write_text("\n".join(lines), encoding="utf-8")


def disk_usage(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def acquire(args: argparse.Namespace) -> int:
    seeds = load_seeds(args.seed)
    if args.ids:
        selected = {base_arxiv_id(item) for item in args.ids}
        seeds = [seed for seed in seeds if seed["arxiv_id"] in selected]
    args.papers_dir.mkdir(parents=True, exist_ok=True)
    client = HttpClient(args.user_agent, args.interval, args.retries, args.timeout)
    records: list[dict[str, Any]] = []
    try:
        metadata = fetch_metadata(client, [seed["arxiv_id"] for seed in seeds])
        enrich_publication_metadata(client, metadata, args.papers_dir)
    except Exception as error:
        metadata = {}
        print(f"metadata batch failed: {error}")
    for index, seed in enumerate(seeds, 1):
        arxiv_id = seed["arxiv_id"]
        print(f"[{index}/{len(seeds)}] {arxiv_id}", flush=True)
        if arxiv_id not in metadata:
            print("  metadata unavailable", flush=True)
            continue
        record = download_one(client, seed, metadata[arxiv_id], args.papers_dir, args.force)
        records.append(record)
        print(f"  PDF={record['pdf_status']} source={record['source_status']} TeX={record['tex_status']}", flush=True)
    write_catalogues(args.papers_dir, seeds, records)
    print(f"Wrote {args.papers_dir / 'manifest.json'}; disk usage={disk_usage(args.papers_dir)} bytes")
    return 0 if len(records) == len(seeds) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=Path, default=Path("papers/seeds.json"))
    parser.add_argument("--papers-dir", type=Path, default=Path("papers"))
    parser.add_argument("--id", dest="ids", action="append", help="acquire only this seed ID (repeatable)")
    parser.add_argument("--force", action="store_true", help="redownload validated existing artifacts")
    parser.add_argument("--interval", type=float, default=3.0, help="minimum seconds between HTTP requests")
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    return parser


def main(argv: list[str] | None = None) -> int:
    return acquire(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
