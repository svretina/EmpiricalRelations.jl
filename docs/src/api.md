# Julia API

The public interface separates publications, empirical relations, and predicted
observables. Relation discovery reads only the packaged registry; it does not load the
raw waveform database.

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
