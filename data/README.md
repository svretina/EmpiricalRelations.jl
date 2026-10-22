# Community BNS postmerger dataset

This directory is the public, CSV-based extraction of the complete 31-paper seed
corpus. It is generated deterministically by `scripts/extract_reference_data.py`
from the preserved arXiv LaTeX source projects.

- `waveforms.csv`: normalized simulation configurations and postmerger measurements.
- `eos.csv`: source-specific EOS identifiers and published stellar properties.
- `sources.csv`: publication-level attribution.
- `extraction_coverage.csv`: per-paper structural and scientific-review coverage.
- `provenance.csv`: exact source table, line, and original LaTeX row for every record.
- `relations/relations.csv`: published empirical-relation inventory.
- `relations/coefficients.csv`: normalized coefficient values and terms.
- `measurements_extra.csv`: sparse paper-specific measurements linked to waveform rows.
- `published_tables.csv`: every detected published LaTeX table with source provenance.
- `published_table_cells.csv`: one lossless row per published table cell, including a
  best-effort numeric value while retaining the original LaTeX.
- `published_equations.csv`: every detected equation environment and its local context.
- `staging/equations.jsonl`: labeled and unlabeled equation environments with context.
- `staging/all_equations.jsonl`: equations structurally extracted from every collected paper.
- `staging/table_inventory.csv`: all detected LaTeX tables, classified as review candidates.
- `staging/table_rows.jsonl`: source-linked raw cells from every detected table.
- `staging/dependencies.csv`: `\input` and `\include` dependency resolution for every paper.
- `validation_report.json`: automated scientific and structural checks.
- `review_issues.csv`: unresolved interpretations requiring human review.

The normative extraction rules are in
[`docs/extraction_conventions.md`](../docs/extraction_conventions.md); canonical
frequency definitions are in
[`docs/frequency_nomenclature.md`](../docs/frequency_nomenclature.md), and paper-local
symbol mappings are in
[`database/notation/paper_frequency_aliases.csv`](../database/notation/paper_frequency_aliases.csv).

Empty frequency cells are missing values, never zero. Their companion status columns
explain whether the source table omitted or did not identify a feature. The standardized
mass ratio is `q = min(m1,m2)/max(m1,m2) <= 1`; the source value and convention are
retained separately.

All 31 collected papers are represented in `sources.csv`, `published_tables.csv`, and/or
`published_equations.csv` according to their source contents. Reviewed adapters normalize
compatible simulation and EOS tables into the compact domain CSVs; the lossless public
exports ensure information from papers with incompatible schemas is still queryable.

Regenerate from the repository root with:

```sh
python3 scripts/extract_reference_data.py
```
