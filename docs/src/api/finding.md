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

The `inputs` filter requires an exact input set; its order is immaterial:

```julia
relations(:f_peak; inputs=[:Lambda_tilde, :M_chirp])
```

The `available` filter instead finds relations whose inputs are a subset of the
variables at hand:

```julia
relations(:f_peak; available=[:M_chirp, :Lambda_tilde, :q])
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

`applicable_relations(quantity; values...)` reports whether each model has all required
inputs and whether the supplied numerical values lie within any documented bounds.
An `unknown` result means that the source did not provide machine-checkable numerical
bounds; it does not establish unrestricted validity.
