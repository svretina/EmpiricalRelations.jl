# Metadata and citations

Every relation carries equation-level provenance and programmatic scientific metadata:

```julia
info(r)
formula(r)
coefficients(r)
domain(r)
source(r)
bibtex(r)
```

`formula(r).original` preserves the expression as transcribed from the publication.
`formula(r).canonical` specializes family placeholders such as ``f_j`` and ``R_x`` to
the selected observable and reference radius. `coefficients(r)` uses the coefficient
symbols from the publication.

`domain(r)` separates machine-checkable numerical bounds from categorical assumptions
and the source's applicability summary. No bounds are inferred when the publication
does not report them.

`source(r)` includes authors, title, year, DOI and arXiv identifiers where available,
the source equation or table, and the extraction path. A publication-level citation
does not require selecting one relation:

```julia
bibtex(:Vretinaris2020)
```

Scientific results should cite the original paper returned by `bibtex(r)`. Cite the
EmpiricalRelations.jl release or repository commit separately to identify the software
and database version used in the calculation.
