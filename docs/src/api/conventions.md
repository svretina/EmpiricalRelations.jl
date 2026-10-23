# Units and symbols

The API uses ordinary Julia numbers and a fixed canonical unit system. Unitful.jl is not
required. Callers are responsible for converting inputs to these units before
evaluation.

## Canonical units

| Physical quantity | API unit |
|---|---|
| Component, total, and chirp masses | ``M_\odot`` |
| Frequencies | kHz |
| Stellar radii | km |
| ``q``, ``\eta``, ``\widetilde{\Lambda}``, and ``\kappa_2^T`` | dimensionless |

Relations published in Hz are converted internally and still return kHz. The canonical
output unit is available as `info(r).output_unit`.

## Input identifiers

| Julia keyword | Meaning |
|---|---|
| `M_tot` | Total gravitational mass ``M_{\mathrm{tot}}`` in ``M_\odot``. |
| `M_chirp` | Chirp mass ``\mathcal{M}`` in ``M_\odot``. |
| `q` | Canonical mass ratio ``\min(m_1,m_2)/\max(m_1,m_2)``. |
| `eta` | Symmetric mass ratio ``m_1m_2/M_{\mathrm{tot}}^2``. |
| `Lambda_tilde` | Effective tidal deformability ``\widetilde{\Lambda}``. |
| `kappa2T` | Quadrupolar tidal coupling constant ``\kappa_2^T``. |
| `R_1_2` | Radius ``R_{1.2}`` in km. |
| `R_1_4` | Radius ``R_{1.4}`` in km. |
| `R_1_6` | Radius ``R_{1.6}`` in km. |
| `R_1_8` | Radius ``R_{1.8}`` in km. |
| `f_peak` | Dominant postmerger spectral frequency in kHz. |
| `f_2_0` | Nonlinear mode-coupling frequency in kHz. |
| `f_spiral` | Spiral-deformation frequency in kHz. |

Reference-radius identifiers are not interchangeable. A relation calibrated with
``R_{1.6}`` must receive `R_1_6`; the registry does not substitute ``R_{1.4}`` or another
radius.

## Output identifiers

The most common output symbols are:

| Identifier | Observable |
|---|---|
| `f_peak` | Dominant Fourier spectral peak. |
| `f_2_0` | Quadrupolar–quasiradial coupling sideband. |
| `f_spiral` | Transient spiral-deformation feature. |
| `f_merger` | Frequency at merger or peak amplitude, as defined by the source. |
| `f_peak_instantaneous` | Instantaneous quadrupolar frequency at the source-defined time. |

These quantities remain distinct even when a publication uses similar notation. See
the [frequency nomenclature](../database/frequency_nomenclature.md) for the complete
mapping policy.

## Mathematical and empirical validity

The evaluator always rejects:

- missing or unexpected inputs;
- non-real or non-finite values;
- non-positive masses, frequencies, radii, and tidal variables;
- mass ratios outside ``0 < q \leq 1``;
- symmetric mass ratios outside ``0 < \eta \leq 1/4``; and
- non-finite results.

These checks establish that the formula is mathematically well-defined. They do not
establish scientific applicability. Calibration bounds and categorical assumptions are
reported separately by `domain(r)`.

An empty numerical bound set means “not encoded or not reported,” not “valid for every
binary.”
