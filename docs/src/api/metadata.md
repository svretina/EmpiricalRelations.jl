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

```julia
expressions = formula(r)
expressions.original
expressions.canonical

fit_coefficients = coefficients(r)
```

The canonical expression is intended for consistent presentation and comparison.
Numerical evaluation calls the tested Julia implementation; it does not parse either
LaTeX string.

`domain(r)` separates machine-checkable numerical bounds from categorical assumptions
and the source's applicability summary. No bounds are inferred when the publication
does not report them.

`source(r)` includes authors, title, year, DOI and arXiv identifiers where available,
the source equation or table, and the extraction path. A publication-level citation
does not require selecting one relation:

```julia
bibtex(:Topolski2023)
```

Useful source fields include:

```julia
s = source(r)
s.title
s.authors
s.year
s.doi
s.arxiv_id
s.url
s.equation_label
s.source_table
s.source_path
```

Fields remain empty or `nothing` when the publication does not provide them; missing
bibliographic details are not fabricated.

Scientific results should cite the original paper returned by `bibtex(r)`. Cite the
EmpiricalRelations.jl release or repository commit separately to identify the software
and database version used in the calculation.

## Metadata for result files

`info(r)` returns a named tuple rather than formatted text:

```julia
metadata = info(r)
metadata.id
metadata.publication
metadata.quantity
metadata.inputs
metadata.output_unit
metadata.verification_status
metadata.implementation_status
```

Derived data products should retain at least the stable relation ID, input values,
output value and unit, and a software release or Git commit.
