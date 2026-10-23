import csv
import ast
import importlib.util
import json
import subprocess
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "docs" / "scripts" / "generate_explorer_data.py"


class ExplorerGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["python3", str(GENERATOR)], cwd=ROOT, check=True)
        cls.output = ROOT / "docs" / "src" / "assets" / "data"

    def test_json_is_valid_and_ids_are_unique(self):
        waveforms = json.loads((self.output / "waveforms.json").read_text())
        self.assertEqual(len(waveforms), len({row["id"] for row in waveforms}))
        self.assertTrue(all(row["source"]["abstract_url"].startswith("https://arxiv.org/abs/") for row in waveforms))
        self.assertTrue(all(row["provenance"] for row in waveforms))

    def test_schema_and_scientific_numbers_are_preserved(self):
        with (ROOT / "data" / "waveforms.csv").open(newline="") as handle:
            csv_rows = list(csv.DictReader(handle))
            columns = set(csv_rows[0])
        json_rows = json.loads((self.output / "waveforms.json").read_text())
        self.assertTrue(columns.issubset(json_rows[0]))
        numeric = ["mtot_msun", "q", "lambda_tilde", "f_peak_khz", "f_2_0_khz", "f_spiral_khz"]
        by_id = {row["id"]: row for row in json_rows}
        for source in csv_rows:
            generated = by_id[source["id"]]
            for key in numeric:
                if source[key] == "":
                    self.assertIsNone(generated[key])
                else:
                    self.assertEqual(Decimal(source[key]), Decimal(str(generated[key])))

    def test_relation_coefficients_and_metadata_counts(self):
        relations = json.loads((self.output / "relations.json").read_text())
        metadata = json.loads((self.output / "metadata.json").read_text())
        self.assertEqual(metadata["counts"]["relations"], len(relations))
        self.assertTrue(all(row["implementation_status"] == "catalogued" for row in relations))
        self.assertTrue(any(row["coefficients"] for row in relations))
        self.assertTrue(all(row["source"]["bibtex"].startswith("@article{") for row in relations))
        self.assertTrue(all(set(row["code"]) == {"julia", "python"} for row in relations))
        for row in relations:
            ast.parse(row["code"]["python"])

    def test_required_static_and_mobile_assets_exist(self):
        css = (ROOT / "docs" / "src" / "assets" / "css" / "database-explorer.css").read_text()
        js = (ROOT / "docs" / "src" / "assets" / "js" / "database-explorer.js").read_text()
        make = (ROOT / "docs" / "make.jl").read_text()
        self.assertIn("@media (max-width: 600px)", css)
        self.assertIn("--er-dialog-bg", css)
        self.assertIn("box-sizing: border-box", css)
        self.assertIn("theme--catppuccin-mocha", css)
        self.assertIn("background: var(--er-dialog-bg) !important", css)
        self.assertIn("showModal", js)
        self.assertIn("sourceLink", js)
        self.assertIn("typesetPromise", js)
        self.assertIn('window.require(["mathjax"]', js)
        self.assertIn("Copy BibTeX", js)
        self.assertIn("er-code-language", js)
        self.assertIn("Documenter.MathJax()", make)


if __name__ == "__main__":
    unittest.main()
