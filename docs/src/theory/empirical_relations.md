# Empirical and quasi-universal relations

An empirical relation summarizes a trend measured in a finite calibration set. In the
postmerger literature, relations connect characteristic frequencies to binary masses,
tidal parameters, cold-star radii, compactness measures, or combinations of them. They
can support inference and model construction, but they are neither raw simulation data
nor exact identities.

## General form

Many catalogued fits can be represented as a linear combination of chosen basis terms,

```math
y(\boldsymbol{x}) = \sum_{k=0}^{p} b_k\,\phi_k(\boldsymbol{x}),
```

where ``y`` is the predicted observable, ``\boldsymbol{x}`` contains independent
variables, ``\phi_k`` are specified terms, and ``b_k`` are calibrated coefficients.
The fit may be linear in its coefficients even when it is nonlinear in the physical
variables. Other relations use explicit nonlinear or piecewise expressions and must be
interpreted in their published form.

Coefficient values are inseparable from:

- the exact mathematical expression and term ordering;
- input and output units;
- any normalization or scale factors;
- the calibration population and EOS sample;
- mass, mass-ratio, tidal, or compactness range;
- the definition of the predicted frequency.

The relations catalogue stores these elements separately so that a numerical
coefficient is never presented without its context.

## Calibration and residuals

For calibration points ``(\boldsymbol{x}_i,y_i)``, a residual may be written

```math
r_i = y_i - \hat y(\boldsymbol{x}_i).
```

Publications report different summaries: maximum absolute residual, mean residual,
standard deviation, root-mean-square error, relative error, or an adjusted coefficient
of determination. These metrics are not interchangeable. Their unit, sign convention,
sample, and weighting must be taken from the original source.

A small in-sample residual does not by itself demonstrate extrapolation accuracy,
universality across numerical methods, or robustness to EOS physics absent from the
calibration set. Correlated simulations from the same EOS family also do not
necessarily constitute independent validation cases.

## Applicability domain

Evaluate a relation only inside its documented domain unless the result is explicitly
treated as an extrapolation. Relevant restrictions can include:

- equal-mass versus unequal-mass binaries;
- a fixed or bounded total-mass range;
- hadronic EOS samples versus phase-transition models;
- non-prompt-collapse remnants;
- a particular spectral definition or time interval;
- source-specific radius or tidal conventions.

The `applicability` and `calibration_population` fields summarize reported restrictions,
while the paper remains authoritative. Missing restrictions are unknown, not evidence
that a relation is universal.

## Measurements, fits, and predictions

The project maintains a strict separation:

| Object | Meaning |
|---|---|
| Numerical measurement | A value obtained from a published simulation analysis |
| Derived parameter | An algebraic transformation of reported values |
| Empirical relation | A published fitted mapping and its calibration metadata |
| Predicted value | The result of evaluating a relation for selected inputs |

Predictions are not inserted into missing measurement cells. Likewise, a relation in
the catalogue is marked `catalogued` until a Julia implementation has been checked
against the published expression, coefficients, units, and reference cases.

## Responsible comparison

When comparing relations, first harmonize the dependent-variable definition and units,
then inspect their calibration domains and residual definitions. A fit for a static
``f_{\mathrm{peak}}`` cannot be compared directly with one for a merger-time or
instantaneous frequency merely because both use the symbol ``f_2``. The
[interactive catalogue](../relations/catalogue.md) exposes the evidence needed for
this comparison without evaluating arbitrary extracted expressions.
