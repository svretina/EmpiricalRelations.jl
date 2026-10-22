import gzip
import io
import json
import sys
import tarfile
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import download_papers as dp


class FakeHeaders(dict):
    def get_content_type(self):
        return self.get("Content-Type", "application/octet-stream").split(";", 1)[0]


class FakeResponse(io.BytesIO):
    def __init__(self, data=b"ok", url="https://example.test/final", content_type="application/octet-stream"):
        super().__init__(data)
        self.headers = FakeHeaders({"Content-Type": content_type})
        self._url = url

    def geturl(self):
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class IdentifierTests(unittest.TestCase):
    def test_valid_identifiers(self):
        for value in ("1910.10856", "1910.10856v3", "hep-th/9901001", "math.GT/0309136v2"):
            self.assertEqual(dp.validate_arxiv_id(value), value)

    def test_invalid_identifiers(self):
        for value in ("", "1910", "https://arxiv.org/abs/1910.10856", "../1910.10856", "1910.10856x"):
            with self.assertRaises(ValueError):
                dp.validate_arxiv_id(value)

    def test_directory_name(self):
        metadata = {
            "arxiv_id": "1910.10856",
            "authors": ["Stamatis Vretinaris", "Someone Else"],
            "submitted": "2019-10-24T00:00:00Z",
            "journal_reference": "Phys. Rev. D 101 (2020)",
        }
        self.assertEqual(dp.directory_name(metadata), "1910.10856_vretinaris_2020")

    def test_duplicate_seeds_are_merged(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "seeds.json"
            path.write_text(json.dumps({"papers": [
                {"arxiv_id": "1910.10856", "topics": ["one"]},
                {"arxiv_id": "1910.10856v2", "topics": ["two"]},
            ]}))
            seeds = dp.load_seeds(path)
        self.assertEqual(len(seeds), 1)
        self.assertEqual(seeds[0]["topics"], ["one", "two"])


class FormatAndExtractionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_pdf_magic_validation_rejects_html(self):
        pdf = self.root / "good.pdf"
        html = self.root / "bad.pdf"
        pdf.write_bytes(b"%PDF-1.7\nbody")
        html.write_bytes(b"<!doctype html><title>rate limited</title>")
        self.assertTrue(dp.valid_pdf(pdf))
        self.assertFalse(dp.valid_pdf(html))

    def test_detect_gzip_tar_plain_tex_and_gzip_tex(self):
        archive = self.root / "archive"
        with tarfile.open(archive, "w:gz") as bundle:
            data = b"\\documentclass{article}"
            info = tarfile.TarInfo("main.tex")
            info.size = len(data)
            bundle.addfile(info, io.BytesIO(data))
        self.assertEqual(dp.detect_source(archive)[0], "gzip_tar")

        tar = self.root / "plain.tar"
        with tarfile.open(tar, "w") as bundle:
            data = b"figure"
            info = tarfile.TarInfo("figure.eps")
            info.size = len(data)
            bundle.addfile(info, io.BytesIO(data))
        self.assertEqual(dp.detect_source(tar)[0], "tar")

        tex = self.root / "source"
        tex.write_text("\\documentclass{article}\n\\begin{document}x\\end{document}")
        self.assertEqual(dp.detect_source(tex)[0], "tex")

        compressed = self.root / "compressed"
        with gzip.open(compressed, "wb") as stream:
            stream.write(tex.read_bytes())
        self.assertEqual(dp.detect_source(compressed)[0], "gzip_tex")

    def test_safe_multifile_extraction_and_root_identification(self):
        archive = self.root / "source.tar.gz"
        with tarfile.open(archive, "w:gz") as bundle:
            files = {
                "project/paper.tex": b"\\documentclass{article}\n\\input{sections/results}\n\\begin{document}x\\end{document}",
                "project/sections/results.tex": b"Result text",
                "project/refs.bib": b"@article{x}",
                "project/figure.png": b"PNG",
            }
            for name, data in files.items():
                info = tarfile.TarInfo(name)
                info.size = len(data)
                bundle.addfile(info, io.BytesIO(data))
        destination = self.root / "source"
        dp.extract_source(archive, "gzip_tar", destination)
        candidates = dp.tex_root_candidates(destination)
        self.assertEqual(candidates[0]["path"], "project/paper.tex")
        inventory = dp.inventory_source(destination)
        self.assertIn("project/refs.bib", inventory["bibliography"])
        self.assertIn("project/figure.png", inventory["figures"])

    def test_path_traversal_and_symlink_are_rejected(self):
        for index, info in enumerate((tarfile.TarInfo("../escape.tex"), tarfile.TarInfo("link"))):
            archive = self.root / f"unsafe{index}.tar"
            if index:
                info.type = tarfile.SYMTYPE
                info.linkname = "/etc/passwd"
            else:
                info.size = 1
            with tarfile.open(archive, "w") as bundle:
                bundle.addfile(info, None if index else io.BytesIO(b"x"))
            with self.assertRaises(dp.UnsafeArchiveError):
                dp.extract_source(archive, "tar", self.root / f"out{index}")

    def test_ambiguous_roots_are_reported(self):
        source = self.root / "source"
        source.mkdir()
        for name in ("a.tex", "b.tex"):
            (source / name).write_text("\\documentclass{article}\n\\begin{document}x\\end{document}")
        candidates = dp.tex_root_candidates(source)
        self.assertEqual(len(candidates), 2)
        self.assertEqual(candidates[0]["score"], candidates[1]["score"])


class NetworkingAndPersistenceTests(unittest.TestCase):
    def test_crossref_publication_date(self):
        payload = json.dumps({"message": {
            "published-print": {"date-parts": [[2012, 1, 6]]},
            "publisher": "APS", "container-title": ["Physical Review Letters"],
        }}).encode()
        client = mock.Mock()
        client.read.return_value = (payload, "application/json", "https://api.crossref.org/works/x")
        result = dp.crossref_publication(client, "10.1234/example")
        self.assertEqual(result["publication_date"], "2012-01-06")
        self.assertEqual(result["publication_year"], 2012)

    def test_retry_after_and_transient_failure(self):
        calls = []
        sleeps = []

        def opener(request, timeout):
            calls.append(request.full_url)
            if len(calls) == 1:
                raise urllib.error.HTTPError(request.full_url, 503, "busy", {"Retry-After": "0"}, None)
            return FakeResponse()

        client = dp.HttpClient(interval=0, retries=2, opener=opener, sleeper=sleeps.append)
        with client.open("https://example.test") as response:
            self.assertEqual(response.read(), b"ok")
        self.assertEqual(len(calls), 2)
        self.assertIn(0.0, sleeps)

    def test_interrupted_download_removes_partial_file(self):
        class Broken(FakeResponse):
            def __init__(self):
                super().__init__(b"")
                self.count = 0

            def read(self, size=-1):
                self.count += 1
                if self.count == 1:
                    return b"partial"
                raise ConnectionError("interrupted")

        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "paper.pdf"
            client = dp.HttpClient(interval=0, retries=0, opener=lambda *args, **kwargs: Broken())
            with self.assertRaises(ConnectionError):
                client.download("https://example.test/pdf", destination, 100)
            self.assertFalse(destination.exists())
            self.assertFalse(Path(str(destination) + ".part").exists())

    def test_existing_checksum_is_idempotently_validated(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "paper.pdf"
            path.write_bytes(b"%PDF-1.7\n")
            metadata = {"checksums": {"pdf_sha256": dp.sha256_file(path)}}
            self.assertTrue(dp.existing_file_valid(path, metadata, "pdf_sha256", dp.valid_pdf))
            path.write_bytes(b"%PDF-1.7\nchanged")
            self.assertFalse(dp.existing_file_valid(path, metadata, "pdf_sha256", dp.valid_pdf))

    def test_missing_source_status_and_metadata_serialization(self):
        metadata = {
            "arxiv_id": "1910.10856", "authors": ["A Author"],
            "submitted": "2019-01-01T00:00:00Z", "journal_reference": None,
            "pdf_url": "https://example.test/pdf", "source_url": "https://example.test/src",
            "title": "Title", "abstract_url": "https://example.test/abs", "categories": [],
        }

        class Client:
            def download(self, url, destination, limit):
                if url.endswith("src"):
                    raise urllib.error.HTTPError(url, 404, "missing", {}, None)
                destination.write_bytes(b"%PDF-1.7\n")
                return url, "application/pdf", destination.stat().st_size

        with tempfile.TemporaryDirectory() as temporary:
            result = dp.download_one(Client(), {"arxiv_id": "1910.10856"}, metadata, Path(temporary))
            self.assertEqual(result["source_status"], "unavailable")
            written = json.loads((Path(temporary) / result["directory"] / "metadata.json").read_text())
            self.assertEqual(written["checksums"]["pdf_sha256"], dp.sha256_file(Path(temporary) / result["directory"] / "paper.pdf"))


if __name__ == "__main__":
    unittest.main()
