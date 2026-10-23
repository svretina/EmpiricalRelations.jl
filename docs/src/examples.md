# Examples

## Evaluate a published relation

```julia
using EmpiricalRelations

r = relation(:Vretinaris2026;
    quantity=:f_2_0,
    inputs=[:M_chirp, :Lambda_tilde],
)

frequency_khz = evaluate(r; M_chirp=1.2, Lambda_tilde=500.0)
```

The relation handle can be reused for a collection of binary configurations:

```julia
systems = [
    (M_chirp=1.18, Lambda_tilde=600.0),
    (M_chirp=1.22, Lambda_tilde=450.0),
]
frequencies_khz = evaluate(r, systems)
```

## Select measured dominant frequencies

```julia
using CSV, DataFrames

waveforms = CSV.read("data/waveforms.csv", DataFrame)
measured = filter(row -> !ismissing(row.f_peak_khz), waveforms)
select(measured, :id, :eos, :mtot_msun, :q, :f_peak_khz, :source_id)
```

## Join a relation to its coefficients

```julia
relations = CSV.read("data/relations/relations.csv", DataFrame)
coefficients = CSV.read("data/relations/coefficients.csv", DataFrame)
fit = relations[1, :]
fit_coefficients = filter(:relation_id => ==(fit.relation_id), coefficients)
```

These table-level examples complement the registry API; they are useful when analysis
requires fields that are not part of numerical evaluation.
