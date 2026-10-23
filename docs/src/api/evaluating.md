# Evaluating relations

Select a relation once and reuse the handle:

```julia
using EmpiricalRelations

r = relation(:Lioutas2021;
    quantity=:f_peak,
    inputs=[:R_1_6],
)

evaluate(r; R_1_6=12.0)
```

Keyword order does not matter. Keyword names do: `info(r).inputs` reports the exact
canonical signature, and `info(r).output_unit` reports the return unit.

Canonical numerical units are:

| Quantity | Unit |
|---|---|
| Mass | solar mass |
| Frequency | kHz |
| Radius | km |
| Tidal deformability and coupling | dimensionless |

Conversions from published Hz expressions are performed inside their evaluator.
Missing, unexpected, non-finite, and nonphysical inputs raise an error. Known
calibration-range violations warn without clipping or modifying the supplied value.
Use `strict_domain=true` to turn that warning into an error, or
`check_domain=false` when intentionally evaluating the mathematical fit outside its
reported range.

Domain checking has three layers:

1. Basic physical checks always reject values such as negative masses, non-finite
   inputs, ``q>1``, or ``\eta>1/4``.
2. Encoded numerical calibration bounds warn by default.
3. Categorical assumptions remain metadata and must be assessed by the researcher.

No evaluation mode clips values to a calibration boundary.

The one-call interface resolves and evaluates through the same implementation:

```julia
predict(:f_peak;
    model=:Kiuchi2020,
    inputs=(:M_tot, :eta, :Lambda_tilde),
    M_tot=2.7,
    eta=0.25,
    Lambda_tilde=400.0,
)
```

For batch calculations, pass a vector of named tuples:

```julia
systems = [
    (R_1_6=11.8,),
    (R_1_6=12.2,),
]
evaluate(r, systems)
```

The named-tuple method avoids requiring DataFrames.jl and is the supported vectorized
interface; Julia does not broadcast keyword arguments element by element.

The batch method applies the same validation to every row. An invalid row stops the
calculation with the same informative error as scalar evaluation. Handle rows
individually when an application needs to retain partial results and record failures.

## Numeric types

Inputs may use standard Julia `Real` types, including higher-precision values where the
published expression supports them:

```julia
evaluate(r; R_1_6=big"12.0")
```

Published decimal coefficients are stored as floating-point values. `BigFloat` inputs
therefore do not create coefficient precision absent from the source.

## Error handling

Missing and extra keywords are rejected to prevent silently applying the wrong relation
signature:

```julia
# Missing R_1_6: raises ArgumentError.
evaluate(r)

# q is not an input of this relation: raises ArgumentError.
evaluate(r; R_1_6=12.0, q=1.0)
```

Inspect `domain(r)` before production evaluation and prefer `strict_domain=true` when
an analysis must remain inside every encoded calibration bound.
