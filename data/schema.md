# Dataset schema

The field definitions below are governed by
[`docs/extraction_conventions.md`](../docs/extraction_conventions.md). Frequency
semantics are further specified by
[`docs/frequency_nomenclature.md`](../docs/frequency_nomenclature.md) and
[`database/notation/paper_frequency_aliases.csv`](../database/notation/paper_frequency_aliases.csv).

## `waveforms.csv`

Masses are in solar masses, postmerger frequencies in kHz, and initial binary GW
frequencies in Hz. `simulation_id` retains the published identifier when one exists;
it is empty for the 2020 CoRe appendix because that table does not provide the original
identifiers. `spectral_type` remains `unknown` unless a source states it explicitly.

The standardized `q` is always the smaller component mass divided by the larger.
`q_original` and `q_original_definition` preserve the table convention. Missing
secondary features use an empty numeric cell plus `f_2_0_status` or
`f_spiral_status`; no empirical relation is used to fill them.

Frequency columns follow `docs/frequency_nomenclature.md`. In particular,
`f_peak_khz` is a static dominant postmerger spectral maximum, while
`f_peak_early_khz`, `f_peak_late_khz`, `f_peak_mean_khz`,
`f_peak_instantaneous_khz`, and `f_merger_khz` remain distinct. Paper-local
symbol mappings and unresolved cases are recorded in
`database/notation/paper_frequency_aliases.csv`.

## `eos.csv`

Each row is a source-specific EOS record. `r_1_2_km` through `r_1_8_km` are radii
of cold, nonrotating stars at the stated masses. They are not remnant radii. Properties
published at other reference masses are retained in `definition_notes` rather than put
in a mismatched radius column.

## Relations

`relations.csv` stores the equation family, variables, calibration population,
applicability, residual statistics, and evidence location. `coefficients.csv` maps
each `b0`–`b5` (or explicit-equation coefficient) to its mathematical term.
The equations are an inventory for review and are not yet a callable Julia API.

## Corpus-wide lossless exports

`published_tables.csv`, `published_table_cells.csv`, and `published_equations.csv` cover
the complete source corpus. The cell table retains both `value_latex` and a cleaned
`value_text`; `numeric_value` is only a convenience extraction of the central number and
must be interpreted with its table header and source context. `measurements_extra.csv`
stores reviewed quantities that do not have a stable column in `waveforms.csv`.

## Provenance and identifiers

Every paper has a stable `arxiv-<identifier>` key in `sources.csv`; all public and
staging records carry that `source_id`. Record IDs extend the source key with a
catalogue- or record-specific suffix. Every public record resolves to a row in
`provenance.csv`, which preserves the original LaTeX cell row and line range.
