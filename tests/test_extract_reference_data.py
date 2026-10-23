import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import extract_reference_data as extraction


class StructuralParserTests(unittest.TestCase):
    def test_conventions_document_records_core_policies(self):
        conventions = (ROOT / "docs/extraction_conventions.md").read_text(encoding="utf-8")
        for policy in (
            "Normalized versus lossless data",
            "q = min(m1,m2) / max(m1,m2) <= 1",
            "Missing numerical data are empty CSV fields, never zero",
            "Different values for the same nominal EOS",
            "Changing a convention",
        ):
            self.assertIn(policy, conventions)

    def test_comments_are_not_parsed_as_rows(self):
        text = r"""
        \begin{table}
        \caption{Example}
        \begin{tabular}{cc}
        name & value \\
        kept & 1.2 \\
        % discarded & 9.9 \\
        \end{tabular}
        \label{table:example}
        \end{table}
        """
        rows = extraction.split_latex_rows(extraction.strip_comments(text))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[-1].cells, ["kept", "1.2"])

    def test_multilevel_cells_do_not_split_inside_braces(self):
        cells = extraction.split_cells(r"\multicolumn{2}{c}{A & B} & 3")
        self.assertEqual(len(cells), 2)
        self.assertEqual(cells[-1], "3")

    def test_missing_numeric_value_remains_none(self):
        self.assertIsNone(extraction.number("-"))
        self.assertEqual(extraction.number(" 2.35 "), 2.35)


class ReferenceExtractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temporary.name) / "data"
        cls.validation = extraction.extract(
            ROOT / "papers/1910.10856_vretinaris_2020/source",
            cls.output,
            ROOT / "papers",
        )

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    @staticmethod
    def read_csv(path):
        with path.open(encoding="utf-8", newline="") as stream:
            return list(csv.DictReader(stream))

    def test_reference_waveform_counts(self):
        rows = self.read_csv(self.output / "waveforms.csv")
        reference = [row for row in rows if row["source_id"] == extraction.SOURCE_ID]
        self.assertGreater(len(rows), 117)
        self.assertEqual(len(reference), 117)
        self.assertEqual(sum(row["catalogue"] == "CFC/SPH" for row in reference), 90)
        self.assertEqual(sum(row["catalogue"] == "CoRe" for row in reference), 27)

    def test_missing_frequencies_are_empty_with_status(self):
        rows = self.read_csv(self.output / "waveforms.csv")
        core = [row for row in rows if row["catalogue"] == "CoRe"]
        self.assertTrue(all(not row["f_2_0_khz"] for row in core))
        self.assertTrue(all(row["f_2_0_status"] == "not_reported_for_catalogue" for row in core))
        self.assertTrue(all(row["f_2_0_khz"] != "0" and row["f_spiral_khz"] != "0" for row in rows))

    def test_eos_registry_preserves_unresolved_variants(self):
        rows = self.read_csv(self.output / "eos.csv")
        rows = [row for row in rows if row["source_id"] == extraction.SOURCE_ID]
        by_name = {row["eos"]: row for row in rows}
        self.assertEqual(len(rows), 18)
        self.assertIn("SHEN", by_name)
        self.assertIn("SLY4", by_name)
        self.assertEqual(by_name["SLY4"]["r_1_4_km"], "")
        self.assertIn("SLy", by_name)

    def test_additional_papers_are_normalized(self):
        rows = self.read_csv(self.output / "waveforms.csv")
        source_ids = {row["source_id"] for row in rows}
        self.assertTrue({
            "arxiv-1106-1616", "arxiv-1908-11418", "arxiv-2411-00943",
            "arxiv-2606-08522",
        } <= source_ids)
        self.assertNotIn("arxiv-2501-11518", source_ids)

    def test_waveform_rows_always_contain_a_frequency(self):
        rows = self.read_csv(self.output / "waveforms.csv")
        self.assertTrue(all(any(row[field] for field in extraction.FREQUENCY_FIELDS) for row in rows))
        retained_ids = {row["id"] for row in rows}
        extras = self.read_csv(self.output / "measurements_extra.csv")
        self.assertTrue(all(row["waveform_id"] in retained_ids for row in extras))

    def test_lossless_public_exports_cover_the_corpus(self):
        sources = {row["source_id"] for row in self.read_csv(self.output / "sources.csv")}
        tables = self.read_csv(self.output / "published_tables.csv")
        equations = self.read_csv(self.output / "published_equations.csv")
        cells = self.read_csv(self.output / "published_table_cells.csv")
        self.assertTrue(cells)
        self.assertTrue(all(row["value_latex"] is not None for row in cells))
        represented = {row["source_id"] for row in tables + equations}
        self.assertGreaterEqual(len(represented & sources), 20)

    def test_frequency_nomenclature_keeps_distinct_definitions(self):
        aliases = self.read_csv(ROOT / "database/notation/paper_frequency_aliases.csv")
        kiuchi = {(row["original_symbol"], row["canonical_quantity"]) for row in aliases if row["arxiv_id"] == "1907.03790"}
        self.assertIn(("f_peak", "f_merger"), kiuchi)
        self.assertIn(("f_2", "f_peak"), kiuchi)
        unresolved_f1 = [row for row in aliases if row["original_symbol"] == "f_1" and row["mapping_status"] == "unresolved"]
        self.assertTrue(unresolved_f1)

        waveforms = self.read_csv(self.output / "waveforms.csv")
        huang = [row for row in waveforms if row["source_id"] == "arxiv-2606-08522"]
        self.assertTrue(any(row["f_peak_mean_khz"] for row in huang))
        self.assertTrue(all(not row["f_peak_khz"] for row in huang))

    def test_relation_and_coefficient_inventory(self):
        relations = self.read_csv(self.output / "relations/relations.csv")
        coefficients = self.read_csv(self.output / "relations/coefficients.csv")
        reference_relations = [row for row in relations if row["source_id"] == extraction.SOURCE_ID]
        self.assertEqual(len(reference_relations), 49)
        self.assertGreater(len(relations), 49)
        reference_coefficients = [row for row in coefficients if row["source_id"] == extraction.SOURCE_ID]
        self.assertEqual(len(reference_coefficients), 291)
        self.assertGreater(len(coefficients), 291)
        self.assertIn("fpeak2DL", {row["equation_label"] for row in relations})
        vretinaris_2026 = [row for row in relations if row["source_id"] == "arxiv-2501-11518"]
        self.assertEqual({row["dependent_variable"] for row in vretinaris_2026}, {"f_2_0_khz", "f_spiral_khz"})

    def test_every_public_record_has_provenance(self):
        waveforms = self.read_csv(self.output / "waveforms.csv")
        eos = self.read_csv(self.output / "eos.csv")
        relations = self.read_csv(self.output / "relations/relations.csv")
        provenance = self.read_csv(self.output / "provenance.csv")
        expected = {row["id"] for row in waveforms + eos} | {row["relation_id"] for row in relations}
        actual = {row["record_id"] for row in provenance}
        self.assertLessEqual(expected, actual)

    def test_all_collected_papers_are_source_registered(self):
        sources = self.read_csv(self.output / "sources.csv")
        coverage = self.read_csv(self.output / "extraction_coverage.csv")
        self.assertEqual(len(sources), extraction.EXPECTED_SOURCE_COUNT)
        self.assertEqual(len(coverage), extraction.EXPECTED_SOURCE_COUNT)
        self.assertEqual(len({row["source_id"] for row in sources}), extraction.EXPECTED_SOURCE_COUNT)
        self.assertEqual({row["source_id"] for row in sources}, {row["source_id"] for row in coverage})
        self.assertTrue(all(row["arxiv_id"] and row["local_source_root"] for row in sources))

    def test_collection_wide_staging_keeps_source_ids(self):
        sources = {row["source_id"] for row in self.read_csv(self.output / "sources.csv")}
        tables = self.read_csv(self.output / "staging/table_inventory.csv")
        equations = [json.loads(line) for line in (self.output / "staging/all_equations.jsonl").read_text().splitlines()]
        self.assertTrue(tables)
        self.assertTrue(equations)
        self.assertLessEqual({row["source_id"] for row in tables}, sources)
        self.assertLessEqual({row["source_id"] for row in equations}, sources)
        self.assertGreaterEqual(len({row["source_id"] for row in tables + equations}), 15)

    def test_validation_documents_published_count_discrepancy(self):
        self.assertEqual(self.validation["status"], "passed_with_warnings")
        warning = next(check for check in self.validation["checks"] if check["status"] == "warning")
        self.assertIn("contains 27 numerical rows", warning["detail"])

    def test_exports_are_deterministic(self):
        before = (self.output / "checksums.json").read_bytes()
        extraction.extract(
            ROOT / "papers/1910.10856_vretinaris_2020/source",
            self.output,
            ROOT / "papers",
        )
        self.assertEqual(before, (self.output / "checksums.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
