# Getting started

The [waveform explorer](database/explorer.md) and [relations catalogue](relations/catalogue.md)
run entirely in your browser. Search terms and filters operate on the generated JSON;
no query is sent to a server.

For programmatic use, clone the repository and read the canonical CSV files directly:

```julia
using DelimitedFiles

header, rows = readdlm("data/waveforms.csv", ',', String, '\n'; header=true)
```

For CSV fields containing commas or quoted text, use a standards-compliant CSV package
such as CSV.jl. Empty numeric fields mean unavailable values, never physical zero.

To build the documentation locally:

```sh
julia --project=docs -e 'using Pkg; Pkg.develop(path="."); Pkg.instantiate()'
julia --project=docs docs/make.jl
python3 -m http.server --directory docs/build 8000
```
