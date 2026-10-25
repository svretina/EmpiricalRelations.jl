# Canonical frequency nomenclature

The database normalizes frequencies by physical definition, not by symbol. Every
paper-specific decision is recorded in
`database/notation/paper_frequency_aliases.csv`. A mapping is local to its cited
paper context; there is intentionally no global rule that every ``f_2``, ``f_1``, or
``f_0`` means the same quantity.

This document specializes the general policies in
[`extraction_conventions.md`](extraction_conventions.md), which is normative for
source evidence, units, missing values, relations, provenance, and review status.

## Canonical quantities

| Identifier | Public column | Definition |
|---|---|---|
| ``f_{\mathrm{peak}}`` | `f_peak_khz` | Dominant peak of the postmerger GW Fourier spectrum, associated with the quadrupolar remnant oscillation. |
| ``f_{2-0}`` | `f_2_0_khz` | Lower sideband identified as nonlinear coupling of the quadrupolar and quasiradial modes. |
| ``f_{\mathrm{spiral}}`` | `f_spiral_khz` | Secondary peak explicitly associated with transient spiral deformation. |
| ``f_0`` | `f_radial_khz` | Quasiradial remnant oscillation frequency. |
| ``f_{\mathrm{peak}}^{\mathrm{early}}`` | `f_peak_early_khz` | Early transient quadrupolar frequency. |
| ``f_{\mathrm{peak}}^{\mathrm{late}}`` | `f_peak_late_khz` | Explicitly defined late-time quadrupolar frequency. |
| ``\overline{f}_{\mathrm{peak}}`` | `f_peak_mean_khz` | Time-averaged dominant quadrupolar frequency. |
| ``f_{\mathrm{peak}}^{\mathrm{inst}}`` | `f_peak_instantaneous_khz` | Instantaneous quadrupolar frequency at a stated time. |
| ``f_{\mathrm{mrg}}`` | `f_merger_khz` | GW frequency at merger or peak amplitude, as defined by the source. |

Additional source quantities remain in `measurements_extra.csv` under controlled
names such as `f_secondary_unknown`, `f_inertial`, or `f_combination_other`.

## Maione et al. (2017), arXiv:1707.03368

The normalized database uses the canonical names above, while the source paper's
symbols and definitions remain explicit. The Fourier and ESPRIT/Prony estimates
are distinct measurement channels and are not substituted for one another.

| Source symbol | Meaning in the paper | Database representation |
|---|---|---|
| ``f_2`` | Dominant quadrupolar peak measured from the full postmerger spectrum; also called ``f_{\rm peak}`` or ``f_p`` in the paper's literature discussion | `f_peak_khz` |
| ``f_{2i}`` | Dominant peak measured from the spectrum through 5 ms after merger | `f_peak_early_khz` |
| ``f_1`` | Measured lower-frequency secondary peak; the proposed physical origin varies by model between spiral emission and other transient/mode-coupling descriptions | `f_secondary_unknown` in `measurements_extra.csv`; deliberately not forced into `f_spiral_khz` or `f_2_0_khz` |
| ``f_3`` | Measured upper transient secondary peak, also discussed as ``f_+`` | `f_combination_other` in `measurements_extra.csv` |
| ``f_0`` | Quasiradial oscillation measured from the maximum-density spectrum over 10 ms from merger | `f_radial_khz` |
| ``f_{\rm merger}`` | Instantaneous GW frequency at maximum strain amplitude | `f_merger_khz` |
| ``f_{20}`` | Relation-derived value ``f_{2i}-f_0`` in the appendix summary, not a directly measured spectral peak | Retained in the lossless table export; not inserted into `f_2_0_khz` |
| ``f_{1,\rm Prony}``, ``f_{2i,\rm Prony}``, ``f_{3,\rm Prony}`` | ESPRIT/Prony components estimated over 1–3 ms after merger | Channel-specific `*_prony` quantities in `measurements_extra.csv` |

The paper's exact header text and every table cell are available in
`published_tables.csv` and `published_table_cells.csv`, principally under labels
`tab:f2`, `tab:f1`, `tab:Prony`, and `tab:FREQ`. The complete mapping, including
source locations and review status, is in
`database/notation/paper_frequency_aliases.csv`. The detailed `tab:f1` values are
used for normalized ``f_1`` measurements; its disagreement with `tab:FREQ` for
three unequal-mass models is recorded in `review_issues.csv` rather than silently
resolved.

## Rules

1. ``f_{\mathrm{peak}}`` is a static spectral maximum; an instantaneous ``f_{22}(t)`` is never put
   in `f_peak_khz`.
2. ``f_{2-0}`` is not calculated from ``f_{\mathrm{peak}}-f_0``; directly reported values are
   independent measurements.
3. A paper's ``f_1`` is not mapped to ``f_{\mathrm{spiral}}`` without an explicit physical
   identification. Ambiguous cases are marked `unresolved`.
4. A parameter named ``f_0`` in a phenomenological model is not a quasiradial mode
   unless the paper defines it that way.
5. Original symbols, cells, equations, units, source paths, and line numbers remain
   available in the lossless published-table/equation exports and provenance files.
6. Different measurement channels and procedures (strain versus `Psi4`, Fourier
   window, time interval, smoothing, or peak fitting) remain part of source notes
   and must be considered before combining records.

The convention follows the physical distinctions used in the
Bauswein–Stergioulas–Vretinaris literature while retaining incompatible notation
from Takami/Rezzolla, Kiuchi, Topolski, and later work explicitly.
