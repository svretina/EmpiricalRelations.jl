# Contributing

Scientific records require a location in the preserved publication source and must
follow the [extraction conventions](database/methodology.md). Generated JSON files are
build artifacts. Changes belong in the extraction code or CSV-generating inputs.

Before opening a pull request:

```sh
python3 scripts/extract_reference_data.py
python3 -m unittest discover -s tests -v
julia --project=. -e 'using Pkg; Pkg.test()'
julia --project=docs docs/make.jl
```

Mark ambiguous notation as `unresolved`; do not assign a normalized frequency without
a definition or physical identification in the publication.
