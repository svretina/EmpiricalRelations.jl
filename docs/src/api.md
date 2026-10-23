# Julia API

The public interface separates publications, empirical relations, and predicted
observables. Relation discovery reads only the packaged registry; it does not load the
raw waveform database.

## Typical workflow

| Task | Function |
|---|---|
| Search the registry | [`relations`](@ref) |
| Select one unambiguous fit | [`relation`](@ref) |
| Evaluate a reusable relation handle | [`evaluate`](@ref) |
| Resolve and evaluate in one call | [`predict`](@ref) |
| Check available inputs and known bounds | [`applicable_relations`](@ref) |
| Inspect identity, inputs, and output unit | [`info`](@ref) |
| Inspect equation and coefficients | [`formula`](@ref), [`coefficients`](@ref) |
| Inspect applicability and provenance | [`domain`](@ref), [`source`](@ref) |
| Retrieve the original citation | [`bibtex`](@ref) |

Begin with [finding relations](api/finding.md), then see
[evaluating relations](api/evaluating.md) and the complete
[research workflows](api/workflows.md). [Units and symbols](api/conventions.md) defines
the numerical interface.

## Registry types

```@docs
RelationID
RelationSpec
RelationCatalogue
EmpiricalRelations.SourceInfo
EmpiricalRelations.DomainSpec
```

## Public functions

```@docs
relations
relation
evaluate
predict
applicable_relations
info
formula
coefficients
domain
source
bibtex
```
