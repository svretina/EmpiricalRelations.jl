# Citations

Explorer records link to the corresponding arXiv entry and list the title, authors, and
DOI when available. Results derived from a measurement or relation should cite its
original publication.

For an evaluated relation, retrieve the publication citation directly:

```julia
bibtex(r)
source(r)
```

`bibtex(:Vretinaris2020)` returns the publication entry without selecting one of its
relations. Cite both the original publication and EmpiricalRelations.jl when software
from this package is used in an analysis. The publication citation attributes the
scientific fit; the repository release or commit identifies the software and database
version used to evaluate it.

The machine-readable bibliography is maintained in
[`papers/bibliography.bib`](https://github.com/svretina/EmpiricalRelations.jl/blob/master/papers/bibliography.bib),
and publication metadata are available in `sources.csv`. Record the repository release
or commit used for an analysis; each documentation build also reports a checksum of the
input tables.
