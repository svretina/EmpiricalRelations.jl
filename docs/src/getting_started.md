# Getting started

Install the package from its repository and inspect the implemented relations:

```julia
using Pkg
Pkg.add(url="https://github.com/svretina/EmpiricalRelations.jl")

using EmpiricalRelations
relations(:f_peak)
```

The package has no runtime dependencies beyond Julia's standard library. Relation
discovery and evaluation use the packaged registry and do not load the waveform CSVs.

## First prediction

```julia
r = relation(:Vretinaris2026;
    quantity=:f_2_0,
    inputs=[:M_chirp, :Lambda_tilde],
)

f_2_0_khz = evaluate(r; M_chirp=1.2, Lambda_tilde=500.0)
```

Inspect the relation before adopting it in an analysis:

```julia
info(r)
formula(r)
coefficients(r)
domain(r)
source(r)
```

The result is in the canonical output unit reported by `info(r).output_unit`. The API
uses kHz for frequencies, solar masses for masses, km for radii, and dimensionless tidal
parameters.

See [finding relations](api/finding.md) for registry filters and
[evaluating relations](api/evaluating.md) for scalar and batch calculations.
The [research workflows](api/workflows.md) cover ambiguity resolution, model comparison,
applicability checks, and provenance-aware result records.

The [waveform explorer](database/explorer.md) and [relations catalogue](relations/catalogue.md)
provide browser-based access to the scientific tables and relation metadata.

For programmatic analysis of the waveform tables, clone the repository and read the CSV
files under `data/`:

```julia
using DelimitedFiles

header, rows = readdlm("data/waveforms.csv", ',', String, '\n'; header=true)
```

Use CSV.jl for fields that contain commas or quoted text. An empty numeric field denotes
an unavailable value, not zero.

To build the documentation locally:

```sh
julia --project=docs -e 'using Pkg; Pkg.develop(path="."); Pkg.instantiate()'
julia --project=docs docs/make.jl
python3 -m http.server --directory docs/build 8000
```
