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

## Predict a radius from a measured frequency

Inverse fits use the same selection and evaluation interface. Here the output unit is
km and the frequency input is kHz:

```julia
inverse_id = Symbol(
    "arxiv-1910-10856-radius-from-frequency-r1-6-f-peak-khz-all-masses",
)
radius_relation = relation(inverse_id)

R_1_6_km = evaluate(radius_relation;
    M_chirp=1.2,
    f_peak=3.0,
)
```

The keyword is `f_peak`, not `f_peak_khz`, because units are part of the API convention
rather than the variable name.

## Evaluate a dimensionless merger relation

Not every output is a frequency. Bernuzzi et al. provide rational fits in terms of the
tidal coupling constant:

```julia
binding_energy_relation = relation(Symbol(
    "arxiv-1504-01764-kappa2t-e-b-textmrg-2",
))

E_b_mrg = evaluate(binding_energy_relation; kappa2T=100.0)
info(binding_energy_relation).output_unit # :dimensionless
```

## Inspect applicability and provenance

```julia
scientific_domain = domain(r)
scientific_domain.summary
scientific_domain.bounds
scientific_domain.assumptions

paper = source(r)
paper.title
paper.arxiv_id
paper.equation_label

write("original-relation.bib", bibtex(r))
```

## Compare calibrations

```julia
models = relations(:f_peak; inputs=[:M_chirp, :R_1_6])

comparison = map(models) do row
    model = relation(row.relation_id)
    (
        relation_id=row.relation_id,
        validity=row.validity,
        f_peak_khz=evaluate(model; M_chirp=1.2, R_1_6=12.0),
    )
end
```

The package deliberately does not rank these predictions. Calibration population and
scientific applicability should determine which relation is appropriate.

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
