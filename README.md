# EmpiricalRelations

[![Build Status](https://github.com/svretina/EmpiricalRelations.jl/actions/workflows/CI.yml/badge.svg?branch=master)](https://github.com/svretina/EmpiricalRelations.jl/actions/workflows/CI.yml?query=branch%3Amaster)

This repository collects and extracts published empirical relations and numerical
measurements for binary-neutron-star postmerger gravitational waves.

[Browse the interactive documentation and database explorer](https://svretina.github.io/EmpiricalRelations.jl/).

The community-readable research products live in [`data/`](data/README.md):

- `waveforms.csv` contains reviewed waveform measurements.
- `eos.csv` contains source-specific EOS properties.
- `relations/` inventories reviewed empirical formulas and coefficients.
- `sources.csv` and `provenance.csv` make every promoted record traceable to its paper.
- `extraction_coverage.csv` tracks structural and scientific-review status for all papers.

The normative extraction and normalization rules are documented in
[`docs/extraction_conventions.md`](docs/extraction_conventions.md). Frequency-specific
definitions and paper-local aliases are documented in
[`docs/frequency_nomenclature.md`](docs/frequency_nomenclature.md).

Regenerate the current exports with:

```sh
python3 scripts/extract_reference_data.py
python3 -m unittest discover -s tests -v
```

Build the documentation locally with:

```sh
julia --project=docs -e 'using Pkg; Pkg.develop(path="."); Pkg.instantiate()'
julia --project=docs docs/make.jl
```
