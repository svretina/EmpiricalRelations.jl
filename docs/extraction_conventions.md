# Data extraction and normalization conventions

This document is the normative record of the conventions used to build the public
dataset. It applies to source acquisition, LaTeX extraction, normalization,
provenance, validation, and review. Paper-specific frequency aliases are recorded
separately in [`database/notation/paper_frequency_aliases.csv`](../database/notation/paper_frequency_aliases.csv),
while the controlled frequency vocabulary is defined in
[`frequency_nomenclature.md`](frequency_nomenclature.md).

When this document conflicts with an older report or comment, this document and the
version-controlled extraction code take precedence.

## 1. Source and evidence policy

- The primary evidence is the versioned arXiv source project recorded in
  `papers/manifest.json`. PDFs are retained for visual checking, but deterministic
  extraction operates on the preserved source files.
- Every paper has a stable `source_id` of the form `arxiv-<id-with-hyphens>`, for
  example `arxiv-1910-10856`.
- Values are transcribed from source tables or explicit equations. We do not digitize
  plots, infer unpublished rows, or fill values from a different paper unless a future
  adapter explicitly documents that operation.
- `\input` and `\include` dependencies are resolved. Files containing table rows
  without an outer `table` environment are represented as included table fragments.
- Original source trees are preserved. Extracted projects are not flattened or
  rewritten.
- The source version, file path, line range, table/equation label, and original LaTeX
  are retained wherever the source format permits.

## 2. Normalized versus lossless data

The extraction has two complementary layers.

### Normalized public records

`waveforms.csv`, `eos.csv`, `measurements_extra.csv`, and `relations/` contain
scientifically reviewed records that can be mapped safely to stable fields. A waveform
row is promoted only when the source reports at least one frequency represented by the
waveform schema. Simulation configurations with no reported frequency remain available
in the lossless table exports instead of appearing as empty frequency records.

### Lossless structural records

`published_tables.csv`, `published_table_cells.csv`, and `published_equations.csv`
retain all structurally detected material, including data that cannot yet be assigned
a common physical meaning. Lossless extraction is not equivalent to scientific
validation.

The normalized layer never replaces the lossless layer. Both are regenerated, and the
coverage table records which papers have reviewed adapters.

## 3. Identifiers and record granularity

- Public IDs are deterministic and begin with the source ID.
- A waveform row describes one published simulation realization or configuration.
- EOS rows are source-specific. Nominally identical EOS names from different papers
  remain separate records.
- Materially different EOS variants or thermal prescriptions are retained through
  `eos_variant` or source-specific notes; they are not silently merged.
- Relations receive a distinct ID for every calibration population, dependent
  variable, fit variant, or coefficient set.
- Cross-paper simulations are not automatically deduplicated. Shared catalogue IDs
  remain traceable to each publication until a documented identity-resolution policy
  is implemented.

## 4. Mass conventions

- Component masses, total mass, and chirp mass are expressed in solar masses.
- The normalized mass ratio is always
  `q = min(m1,m2) / max(m1,m2) <= 1`.
- `q_original` and `q_original_definition` preserve the source value and convention.
- If a source reports total or average mass together with a mass ratio, component
  masses may be algebraically reconstructed only when the source convention is
  explicit. The row notes state that the masses were derived.
- Chirp mass may be calculated from published component masses. A source-tabulated
  chirp mass is retained when available, subject to rounding validation.
- Masses are never inferred from an EOS name or from a frequency relation.

## 5. Frequency conventions

- All normalized frequency columns ending in `_khz` use kHz.
- `f_peak_khz` is reserved for a static dominant postmerger Fourier-spectrum peak.
- Merger-time, early, late, mean, instantaneous, radial, and secondary frequencies
  remain separate quantities. Similar notation alone is insufficient for a mapping.
- A source's `f_peak` can map to `f_merger` when the paper defines it at maximum strain
  amplitude, as in Kiuchi et al. Conversely, a source's `f2` can map to canonical
  `f_peak` when it is explicitly the dominant postmerger spectral maximum.
- `f1` is not automatically mapped to `f_spiral` or `f_2_0`.
- The physical approximation `f_2-0 ≈ f_peak - f_radial` is never used to fill a
  missing measurement.
- A phenomenological parameter named `f0` is not treated as a quasiradial mode without
  source evidence.
- Original symbols, definitions, units, and mapping decisions remain in the alias
  registry, source cells, equations, notes, and provenance.

## 6. Units and numeric values

- Component and total masses: `M_sun`.
- Stellar radii: km.
- Normalized postmerger and merger frequency columns: kHz.
- `f_gw_initial_hz`: Hz, because that is the explicit schema field.
- Relation units are stored per dependent variable and residual rather than assumed
  globally.
- Published table cells retain `value_latex` and `value_text`. `numeric_value` is only
  the first central numeric token extracted for convenience; it is not a substitute
  for interpreting the table header.
- Parenthetical or asymmetric uncertainties remain in the original cell text even
  when the central value is promoted. They are not discarded conceptually or replaced
  by zero.
- Header scale factors such as `×10²` are applied when normalizing coefficients, and
  this decision is stated in relation notes.
- No unit conversion is performed unless both source and target units are known.

## 7. Missing values and status fields

- Missing numerical data are empty CSV fields, never zero.
- A simulation row with every frequency field empty is excluded from `waveforms.csv`;
  its source table remains in the lossless exports.
- A literal zero is retained only when the source reports a physical zero.
- Status fields distinguish at least `measured`, `not_reported`, `not_identified`,
  catalogue-level omission, prompt collapse, and no collapse where the adapter has
  enough evidence.
- A dash, ellipsis, cross, or blank source cell is interpreted using its caption and
  surrounding text. The raw cell remains available regardless of normalization.
- No empirical relation is used to impute a missing raw measurement.
- Conflicting narrative and table counts are reported as review issues; absent records
  are not synthesized.

## 8. EOS conventions

- EOS identifiers preserve the source spelling sufficiently to distinguish variants;
  cosmetic LaTeX and citations may be removed.
- EOS properties are values for cold, nonrotating stellar models unless a record says
  otherwise.
- A radius is stored only in the matching reference-mass column. For example,
  `R_1.35` is not put into `r_1_4_km`; properties without a schema column remain in
  `definition_notes` or the lossless table export.
- Different values for the same nominal EOS in different papers are not overwritten
  or averaged.
- If an EOS occurs in a normalized waveform table without a compatible property row,
  a source-linked registry row is created with empty properties.

## 9. Empirical-relation conventions

- `relations.csv` stores one row per reviewed published fit and calibration variant.
- `coefficients.csv` stores coefficient values separately with explicit mathematical
  terms and a foreign key to the relation.
- The original LaTeX equation is retained. Canonical variable names supplement rather
  than rewrite the source expression.
- Calibration population, applicability domain, source path, residual definition, and
  units are recorded when the source supplies them.
- Original fits are distinguished from papers that merely reuse or assess an earlier
  relation. Reused formulas may appear in the lossless equation inventory without
  being promoted as a new calibrated relation.
- A time-mean, instantaneous, merger, or isolated-star frequency relation is not
  relabeled as a static postmerger-peak relation.
- Coefficients embedded in equations can be normalized when their terms and scaling
  are unambiguous. Otherwise the equation remains lossless and awaits review.

## 10. Provenance and review status

- Every normalized waveform, EOS, and relation record must resolve to
  `provenance.csv`.
- `verified` or `verified_from_*` means a paper-specific adapter was checked against
  the source table/equation and its scientific context.
- `normalized_table_adapter` in `extraction_coverage.csv` means at least one structure
  from that paper was promoted through a reviewed adapter.
- `lossless_structural_extraction` means tables/equations were preserved but not given
  paper-specific semantics.
- `structurally_extracted_unreviewed` is a candidate, not an endorsed scientific
  interpretation.
- Ambiguous nomenclature mappings use `mapping_status=unresolved` and must not populate
  a more specific canonical field.

## 11. Validation and reproducibility

- Regeneration must be deterministic for unchanged source projects and extraction
  code.
- IDs must remain unique, coefficients must resolve to relations, public records must
  resolve to provenance, and staging records must resolve to registered sources.
- Derived chirp masses and normalized mass ratios are checked against published values
  within table-rounding tolerance where both exist.
- Exact source discrepancies remain warnings with documented resolutions rather than
  being hidden or repaired speculatively.
- `data/checksums.json` covers generated data products. Tests exercise parser behavior,
  source registration, deterministic regeneration, nomenclature distinctions, and
  provenance coverage.
- After code changes, regenerate the dataset, run the Python and Julia tests, and
  rebuild the Graphify code graph.

## 12. Changing a convention

A convention change should update, in the same commit:

1. This document and, if relevant, `frequency_nomenclature.md`.
2. The paper-local alias registry.
3. The extraction adapter and schema documentation.
4. Tests demonstrating the changed interpretation and guarding against regression.
5. Regenerated CSV/JSON products and checksums.

Changes that alter physical meaning should be treated as schema migrations even when
the CSV column names do not change.
