# Corpus extraction report

Sources: 31-paper BNS postmerger seed corpus, with Vretinaris, Stergioulas & Bauswein (2020) as the reference adapter.

Governing policies: [`docs/extraction_conventions.md`](../docs/extraction_conventions.md). Frequency vocabulary: [`docs/frequency_nomenclature.md`](../docs/frequency_nomenclature.md).

## Extracted structures

- `CFC/SPH`: `tables/bauswein_data.tex`; latex_rows=45, waveform_records=90
- `CoRe`: `tables/CORE_data.tex`; latex_rows=27, waveform_records=27
- `EOS`: `tables/TOV_info.tex`; eos_records=16
- `frequency_relations`: `tables/tables_combined_fRM.tex`; relation_records=24
- `radius_relations`: `tables/tables_combined.tex`; relation_records=24

## Count investigation

The CFC/SPH appendix table contains 45 physical LaTeX rows with two waveform entries per row, yielding the stated 90 records.
The manuscript narrative states that 28 CoRe waveforms were used, but `tables/CORE_data.tex` contains only 27 numerical rows. No omitted row can be reconstructed from the published table, so `waveforms.csv` contains 27 CoRe records and `review_issues.csv` records the discrepancy.
The CFC/SPH text states 13 EOS while the frequency table contains 12 unique identifiers. SHEN and SLY4 have no row in `TOV_info.tex`; they remain distinct EOS registry entries with missing properties rather than being aliased or filled.

## Interpretation policy

Dashes in CFC/SPH secondary-frequency cells are retained as missing with status `not_reported_or_not_identified`. CoRe secondary frequencies are missing with status `not_reported_for_catalogue`, because the manuscript explicitly says only the dominant frequency was extracted for that subset. Spectral classes are not inferred from peak presence.

Validation status: **passed_with_warnings**.

## Collection-wide structural coverage

The source registry contains 31 papers. The generic pass found 93 tables, 1412 table rows, 485 equations, and 27 input/include dependencies. Every detected table cell and equation is published with source IDs and line numbers. Reviewed paper adapters additionally normalize compatible waveform and EOS records; other records retain their original text rather than receiving guessed semantics.
