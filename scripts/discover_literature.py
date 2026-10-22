#!/usr/bin/env python3
"""Build a review-only BNS postmerger candidate bibliography with OpenAlex."""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


QUERIES = [
    "binary neutron star postmerger gravitational wave frequency",
    "fpeak f2 neutron star merger empirical relation",
    "binary neutron star postmerger waveform model",
    "secondary frequencies spiral mode neutron star merger",
    "thermal phase transition postmerger gravitational waves",
    "unequal mass spin postmerger frequency neutron star",
]
CORE_IDS = {"1502.03176", "1604.00246", "1910.10856", "2111.08353", "2205.09112"}
ARXIV_RE = re.compile(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})", re.I)


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class OpenAlex:
    def __init__(self, email: str, interval: float = 0.2):
        self.email = email
        self.interval = interval
        self.last = 0.0

    def get(self, path: str, **parameters: Any) -> dict[str, Any]:
        delay = self.interval - (time.monotonic() - self.last)
        if delay > 0:
            time.sleep(delay)
        parameters["mailto"] = self.email
        url = "https://api.openalex.org/" + path + "?" + urllib.parse.urlencode(parameters)
        request = urllib.request.Request(url, headers={"User-Agent": f"EmpiricalRelations.jl discovery (mailto:{self.email})"})
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.load(response)
        self.last = time.monotonic()
        return payload


def abstract_text(work: dict[str, Any]) -> str:
    inverted = work.get("abstract_inverted_index") or {}
    positions = [(position, word) for word, values in inverted.items() for position in values]
    return " ".join(word for _, word in sorted(positions))


def arxiv_id(work: dict[str, Any]) -> str | None:
    for location in work.get("locations") or []:
        for value in (location.get("landing_page_url"), location.get("pdf_url")):
            match = ARXIV_RE.search(value or "")
            if match:
                return match.group(1)
    return None


def relevant(work: dict[str, Any]) -> bool:
    text = (work.get("title", "") + " " + abstract_text(work)).lower().replace("post-merger", "postmerger")
    compact = re.sub(r"[^a-z0-9]+", " ", text)
    neutron_merger = ("neutron star" in text or "bns" in compact.split()) and "merger" in text
    postmerger = any(term in text for term in (
        "postmerger", "post merger", "merger remnant", "f_peak", "fpeak", "f_2", "f2 ",
        "spiral mode", "secondary frequenc", "threshold mass", "kilohertz gravitational",
    ))
    return neutron_merger and postmerger


def compact_work(work: dict[str, Any], origins: set[str]) -> dict[str, Any]:
    authors = [entry.get("author", {}).get("display_name") for entry in work.get("authorships", [])]
    authors = [author for author in authors if author]
    primary = work.get("primary_location") or {}
    source = primary.get("source") or {}
    return {
        "openalex_id": work.get("id"),
        "arxiv_id": arxiv_id(work),
        "doi": (work.get("doi") or "").removeprefix("https://doi.org/") or None,
        "title": work.get("title"),
        "authors": authors,
        "publication_year": work.get("publication_year"),
        "publication_date": work.get("publication_date"),
        "venue": source.get("display_name"),
        "landing_page_url": primary.get("landing_page_url") or work.get("id"),
        "cited_by_count": work.get("cited_by_count", 0),
        "discovery_routes": sorted(origins),
        "review_status": "candidate",
        "downloaded": False,
    }


def resolve_core_works(api: OpenAlex, seeds: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    output = {}
    for seed in seeds:
        if seed["arxiv_id"] not in CORE_IDS:
            continue
        doi = seed.get("doi")
        try:
            if doi:
                work = api.get("works/https://doi.org/" + urllib.parse.quote(doi, safe="/"))
            else:
                result = api.get("works", search=seed["title"], **{"per-page": 1})
                work = result["results"][0]
            output[seed["arxiv_id"]] = work
        except Exception as error:
            print(f"core resolution failed for {seed['arxiv_id']}: {error}")
    return output


def discover(api: OpenAlex, manifest: dict[str, Any], per_query: int, max_candidates: int) -> dict[str, Any]:
    seeds = manifest["papers"]
    seed_arxiv = {item["arxiv_id"] for item in seeds}
    seed_dois = {item.get("doi", "").lower() for item in seeds if item.get("doi")}
    found: dict[str, tuple[dict[str, Any], set[str]]] = {}

    def add(work: dict[str, Any], route: str) -> None:
        identity = work.get("id")
        if not identity or arxiv_id(work) in seed_arxiv or (work.get("doi") or "").removeprefix("https://doi.org/").lower() in seed_dois:
            return
        if not relevant(work):
            return
        if identity not in found:
            found[identity] = (work, set())
        found[identity][1].add(route)

    for query in QUERIES:
        try:
            response = api.get("works", search=query, filter="from_publication_date:2010-01-01", **{"per-page": per_query})
            for work in response.get("results", []):
                add(work, "keyword:" + query)
        except Exception as error:
            print(f"search failed for {query!r}: {error}")

    core = resolve_core_works(api, seeds)
    for seed_id, work in core.items():
        openalex_id = work["id"].rsplit("/", 1)[-1]
        try:
            response = api.get("works", filter=f"cites:{openalex_id}", sort="cited_by_count:desc", **{"per-page": per_query})
            for candidate in response.get("results", []):
                add(candidate, f"cites:{seed_id}")
        except Exception as error:
            print(f"citation search failed for {seed_id}: {error}")
        reference_ids = [value.rsplit("/", 1)[-1] for value in work.get("referenced_works", [])[:50]]
        if reference_ids:
            try:
                response = api.get("works", filter="openalex_id:" + "|".join(reference_ids), **{"per-page": 50})
                for candidate in response.get("results", []):
                    add(candidate, f"referenced_by:{seed_id}")
            except Exception as error:
                print(f"reference lookup failed for {seed_id}: {error}")

    candidates = [compact_work(work, origins) for work, origins in found.values()]
    candidates.sort(key=lambda item: (-len(item["discovery_routes"]), -item["cited_by_count"], -(item["publication_year"] or 0), item["title"] or ""))
    discovered_relevant_count = len(candidates)
    candidates = candidates[:max_candidates]
    return {
        "schema_version": 1,
        "generated_at": now(),
        "source": "OpenAlex keyword, citation, and reference searches",
        "seed_count": len(seeds),
        "discovered_relevant_count": discovered_relevant_count,
        "candidate_count": len(candidates),
        "automatic_selection_note": "Candidates passed a conservative title/abstract relevance filter and require human review before acquisition.",
        "queries": QUERIES,
        "candidates": candidates,
    }


def write_bibliography(path: Path, candidates: list[dict[str, Any]]) -> None:
    lines = ["% Review-only candidate bibliography generated from OpenAlex.", ""]
    for index, item in enumerate(candidates, 1):
        surname = re.sub(r"[^a-z0-9]", "", (item["authors"][0].split()[-1] if item["authors"] else "unknown").lower())
        key = f"{surname}{item.get('publication_year') or 'unknown'}candidate{index}"
        fields = {
            "title": item.get("title"), "author": " and ".join(item.get("authors", [])),
            "year": item.get("publication_year"), "doi": item.get("doi"), "eprint": item.get("arxiv_id"),
            "archivePrefix": "arXiv" if item.get("arxiv_id") else None, "url": item.get("landing_page_url"),
        }
        lines.append(f"@article{{{key},")
        for name, value in fields.items():
            if value:
                lines.append(f"  {name} = {{{str(value).replace('{', '').replace('}', '')}}},")
        lines.extend(["}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("papers/manifest.json"))
    parser.add_argument("--output", type=Path, default=Path("papers/candidates.json"))
    parser.add_argument("--bibliography", type=Path, default=Path("papers/candidates.bib"))
    parser.add_argument("--email", default="svretina@gmail.com")
    parser.add_argument("--per-query", type=int, default=50)
    parser.add_argument("--max-candidates", type=int, default=75)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    result = discover(OpenAlex(args.email), manifest, args.per_query, args.max_candidates)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_bibliography(args.bibliography, result["candidates"])
    print(f"Wrote {len(result['candidates'])} review candidates to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
