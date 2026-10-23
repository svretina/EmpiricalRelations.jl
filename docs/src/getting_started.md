# Getting started

The [waveform explorer](database/explorer.md) and [relations catalogue](relations/catalogue.md)
load generated JSON files and apply search and filters in the browser.

For programmatic analysis, clone the repository and read the CSV files under `data/`:

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
