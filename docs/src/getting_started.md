# Getting started

Install the package from its repository and inspect the implemented relations:

```julia
using Pkg
Pkg.add(url="https://github.com/svretina/EmpiricalRelations.jl")

using EmpiricalRelations
relations(:f_peak)
```

See [finding relations](api/finding.md) for registry filters and
[evaluating relations](api/evaluating.md) for scalar and batch calculations.

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
