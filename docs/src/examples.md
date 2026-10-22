# Examples

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

These examples inspect catalogue data. They do not evaluate a relation or turn a
published fit into a validated package implementation.
