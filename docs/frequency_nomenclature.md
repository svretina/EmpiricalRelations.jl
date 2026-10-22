# Canonical frequency nomenclature

The database normalizes frequencies by physical definition, not by symbol. Every
paper-specific decision is recorded in
`database/notation/paper_frequency_aliases.csv`. A mapping is local to its cited
paper context; there is intentionally no global rule that every `f2`, `f1`, or
`f0` means the same quantity.

This document specializes the general policies in
[`extraction_conventions.md`](extraction_conventions.md), which is normative for
source evidence, units, missing values, relations, provenance, and review status.

## Canonical quantities

| Identifier | Public column | Definition |
|---|---|---|
| `f_peak` | `f_peak_khz` | Dominant peak of the postmerger GW Fourier spectrum, associated with the quadrupolar remnant oscillation. |
| `f_2_0` | `f_2_0_khz` | Lower sideband identified as nonlinear coupling of the quadrupolar and quasiradial modes. |
| `f_spiral` | `f_spiral_khz` | Secondary peak explicitly associated with transient spiral deformation. |
| `f_radial` | `f_radial_khz` | Quasiradial remnant oscillation frequency. |
| `f_peak_early` | `f_peak_early_khz` | Early transient quadrupolar frequency. |
| `f_peak_late` | `f_peak_late_khz` | Explicitly defined late-time quadrupolar frequency. |
| `f_peak_mean` | `f_peak_mean_khz` | Time-averaged dominant quadrupolar frequency. |
| `f_peak_instantaneous` | `f_peak_instantaneous_khz` | Instantaneous quadrupolar frequency at a stated time. |
| `f_merger` | `f_merger_khz` | GW frequency at merger or peak amplitude, as defined by the source. |

Additional source quantities remain in `measurements_extra.csv` under controlled
names such as `f_secondary_unknown`, `f_inertial`, or `f_combination_other`.

## Rules

1. `f_peak` is a static spectral maximum; an instantaneous `f22(t)` is never put
   in `f_peak_khz`.
2. `f_2-0` is not calculated from `f_peak-f_radial`; directly reported values are
   independent measurements.
3. A paper's `f1` is not mapped to `f_spiral` without an explicit physical
   identification. Ambiguous cases are marked `unresolved`.
4. A parameter named `f0` in a phenomenological model is not a quasiradial mode
   unless the paper defines it that way.
5. Original symbols, cells, equations, units, source paths, and line numbers remain
   available in the lossless published-table/equation exports and provenance files.
6. Different measurement channels and procedures—strain versus `Psi4`, Fourier
   window, time interval, smoothing, or peak fitting—remain part of source notes
   and must be considered before combining records.

The convention follows the physical distinctions used in the
Bauswein–Stergioulas–Vretinaris literature while retaining incompatible notation
from Takami/Rezzolla, Kiuchi, Topolski, and later work explicitly.
