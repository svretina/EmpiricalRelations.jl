# Contributing

Scientific additions should begin with preserved primary-source evidence and follow the
[extraction conventions](database/methodology.md). Do not edit generated browser JSON;
change the canonical extraction inputs or adapter and rebuild instead.

Before opening a pull request:

```sh
python3 scripts/extract_reference_data.py
python3 -m unittest discover -s tests -v
julia --project=. -e 'using Pkg; Pkg.test()'
julia --project=docs docs/make.jl
```

Report ambiguous notation as unresolved rather than forcing it into a canonical field.
