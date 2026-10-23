# Evaluating relations

Select a relation once and reuse the handle:

```julia
using EmpiricalRelations

r = relation(:Vretinaris2026;
    quantity=:f_2_0,
    inputs=[:M_chirp, :Lambda_tilde],
)

evaluate(r; M_chirp=1.2, Lambda_tilde=500.0)
```

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

The one-call interface resolves and evaluates through the same implementation:

```julia
predict(:f_2_0;
    model=:Vretinaris2026,
    inputs=(:M_chirp, :Lambda_tilde),
    M_chirp=1.2,
    Lambda_tilde=500.0,
)
```

For batch calculations, pass a vector of named tuples:

```julia
systems = [
    (M_chirp=1.18, Lambda_tilde=600.0),
    (M_chirp=1.22, Lambda_tilde=450.0),
]
evaluate(r, systems)
```

Scalar calls can also use Julia broadcasting when each keyword is supplied as a
scalar call, while the named-tuple method avoids requiring DataFrames.jl.
