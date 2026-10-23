# Finding relations

`relations()` returns a lightweight table with stable relation IDs, publications,
predicted quantities, required inputs, applicability summaries, and implementation
status.

```julia
using EmpiricalRelations

relations()
relations(:f_peak)
relations(:f_2_0)
relations(author="Vretinaris")
relations(publication=:Bernuzzi2015)
```

The catalogue supports `length`, indexing, iteration, and collection. Each row is a
named tuple with fields `relation_id`, `publication`, `quantity`, `inputs`, `validity`,
and `status`:

```julia
catalogue = relations(:f_peak)
first_row = catalogue[1]

for row in catalogue
    println(row.relation_id, " — ", row.publication)
end
```

Use the stable `relation_id` in stored analyses and configuration files.

The `inputs` filter requires an exact input set; its order is immaterial:

```julia
relations(:f_peak; inputs=[:Lambda_tilde, :M_chirp])
```

The `available` filter instead finds relations whose inputs are a subset of the
variables at hand:

```julia
relations(:f_peak; available=[:M_chirp, :Lambda_tilde, :q])
```

`inputs` describes the model wanted, whereas `available` describes the data available.
Author matching is case-insensitive and searches every author attached to the source:

```julia
relations(author="vretinaris")
```

Select a unique relation using a publication, observable, and input signature:

```julia
r = relation(:Vretinaris2026;
    quantity=:f_2_0,
    inputs=[:M_chirp, :Lambda_tilde],
)
```

Some publications report several fits with the same observable and input signature,
for example separate calibration populations. In that case `relation` reports the
candidate stable IDs rather than selecting one implicitly. Pass one of those IDs to
`relation` to make the choice explicit.

```julia
candidates = relations(:f_peak;
    publication=:Vretinaris2020,
    inputs=[:M_chirp, :R_1_6],
)

r = relation(candidates[1].relation_id)
```

The indexing above only demonstrates the interface. Before storing a stable ID, inspect
the candidate's `validity` and choose the intended calibration population.

`applicable_relations(quantity; values...)` reports whether each model has all required
inputs and whether the supplied numerical values lie within any documented bounds.
An `unknown` result means that the source did not provide machine-checkable numerical
bounds; it does not establish unrestricted validity.

## Canonical names and aliases

Public results use canonical names such as `:M_chirp`, `:Lambda_tilde`, and `:R_1_6`.
Common database-column spellings—including `:mchirp_msun`, `:lambda_tilde`, and
`:r_1_6_km`—are accepted in discovery filters. Evaluation keywords use the canonical
names reported by the selected relation.

## Common selection errors

- “No relation matches” means that the publication, quantity, inputs, or stable ID did
  not identify an inventory entry. Filter one dimension at a time to inspect the
  available choices.
- “Multiple relations match” means the selection is scientifically ambiguous. The
  error lists stable IDs that can be inspected and selected explicitly.
- `implemented_only=true` is the default. Set it to `false` when inspecting an inventory
  that may also contain catalogued but non-callable relations.
