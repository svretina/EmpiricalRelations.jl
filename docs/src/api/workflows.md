# Research workflows

This page collects complete examples that can be adapted to scripts, notebooks, and
parameter-estimation pipelines. The registry is lightweight and independent of the raw
waveform database.

## Discover, select, evaluate, and cite

Start with the physical observable and the parameters available in the analysis:

```julia
using EmpiricalRelations

catalogue = relations(:f_peak;
    available=[:M_tot, :eta, :Lambda_tilde],
)
```

The returned `RelationCatalogue` behaves like a vector of named tuples. Each row has a
stable `relation_id`, publication, output quantity, input tuple, validity summary, and
implementation status.

```julia
for row in catalogue
    println(row.publication, "  ", row.inputs, "  ", row.relation_id)
end
```

Select a model using scientific metadata rather than array position:

```julia
r = relation(:Kiuchi2020;
    quantity=:f_peak,
    inputs=[:M_tot, :eta, :Lambda_tilde],
)

f_peak_khz = evaluate(r;
    M_tot=2.7,
    eta=0.25,
    Lambda_tilde=400.0,
)
```

Record the exact relation and its source alongside the prediction:

```julia
result = (
    relation_id=info(r).id,
    prediction=f_peak_khz,
    unit=info(r).output_unit,
    publication=info(r).publication,
    arxiv=source(r).arxiv_id,
)

write("relation.bib", bibtex(r))
```

## Use a stable relation ID

A publication may provide distinct fits for equal-mass and broader calibration sets.
The following query intentionally returns more than one relation:

```julia
candidates = relations(:f_peak;
    publication=:Vretinaris2020,
    inputs=[:M_chirp, :R_1_6],
)
```

Inspect the `validity` and `relation_id` columns, then select the intended calibration
explicitly:

```julia
all_masses_id = Symbol(
    "arxiv-1910-10856-frequency-from-radius-f-peak-khz-r1-6-all-masses",
)
r = relation(all_masses_id)
evaluate(r; M_chirp=1.2, R_1_6=12.0)
```

Stable IDs are preferable in reproducible pipelines because they remain unambiguous as
new publications and fit variants are added.

## Compare models with the same signature

Use `relations(...; inputs=...)` to compare only like-for-like models:

```julia
models = relations(:f_merger;
    inputs=[:M_tot, :q, :kappa2T],
)

comparison = [
    (
        publication=row.publication,
        relation_id=row.relation_id,
        prediction_khz=evaluate(
            relation(row.relation_id);
            M_tot=2.7,
            q=0.9,
            kappa2T=100.0,
        ),
    )
    for row in models
]
```

The registry does not rank models or select a preferred relation from residuals. Model
choice remains an explicit scientific decision involving calibration population,
domain, waveform definition, and the source publication.

## Evaluate a parameter sample

The batch interface accepts a vector of named tuples and returns one prediction per
row:

```julia
r = relation(:Lioutas2021;
    quantity=:f_peak,
    inputs=[:R_1_6],
)

posterior_samples = [
    (R_1_6=11.8,),
    (R_1_6=12.0,),
    (R_1_6=12.2,),
]

f_peak_khz = evaluate(r, posterior_samples)
```

The method accepts standard Julia `Real` values, including `Float64` and `BigFloat`.
DataFrames are not required. When working with a DataFrame, convert the required columns
to named tuples or evaluate each row explicitly.

## Check applicability before evaluation

`relations(...; available=...)` checks only whether the required variables are present.
`applicable_relations` additionally reports known numerical-domain status:

```julia
statuses = applicable_relations(:f_peak;
    M_tot=2.7,
    q=0.9,
    kappa2T=100.0,
)

evaluable = filter(row -> row.inputs_available, statuses)
```

Possible `domain_status` values are:

| Status | Meaning |
|---|---|
| `:within` | The supplied values satisfy every encoded numerical bound. |
| `:outside` | At least one supplied value violates an encoded bound. |
| `:unknown` | The relation has no machine-checkable numerical bounds. |
| `:missing_inputs` | Some required variables were not supplied. |

Categorical assumptions—such as EOS set, mass population, spin assumptions, or remnant
class—cannot generally be inferred from numerical keywords. Inspect `domain(r)` before
using a relation in an analysis.

## Control extrapolation behavior

Known calibration-domain violations emit a warning and still evaluate the mathematical
fit:

```julia
value = evaluate(r; parameters...)
```

For production analyses, make known violations fatal:

```julia
value = evaluate(r; parameters..., strict_domain=true)
```

Set `check_domain=false` only when extrapolation is intentional and documented:

```julia
value = evaluate(r; parameters..., check_domain=false)
```

No mode clips inputs or substitutes a boundary value.

## One-call prediction

`predict` is convenient when a relation handle will not be reused:

```julia
E_b_mrg = predict(:E_b_mrg;
    model=:Bernuzzi2015,
    inputs=(:kappa2T,),
    kappa2T=100.0,
)
```

It resolves the model and delegates to `evaluate`; it does not maintain a second copy of
the numerical expression.

## Preserve provenance with derived results

A compact record for an exported prediction can include:

```julia
prediction_record = (
    relation_id=info(r).id,
    publication=info(r).publication,
    inputs=(R_1_6=12.0,),
    value=evaluate(r; R_1_6=12.0),
    unit=info(r).output_unit,
    equation=source(r).equation_label,
    arxiv_id=source(r).arxiv_id,
)
```

This is preferable to storing only the publication name because one publication may
contain several relations for the same observable.
