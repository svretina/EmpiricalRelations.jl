# EmpiricalRelations.jl

[![CI](https://github.com/svretina/EmpiricalRelations.jl/actions/workflows/CI.yml/badge.svg?branch=master)](https://github.com/svretina/EmpiricalRelations.jl/actions/workflows/CI.yml?query=branch%3Amaster)
[![Documentation](https://github.com/svretina/EmpiricalRelations.jl/actions/workflows/Documentation.yml/badge.svg?branch=master)](https://github.com/svretina/EmpiricalRelations.jl/actions/workflows/Documentation.yml?query=branch%3Amaster)
[![Documentation site](https://img.shields.io/badge/docs-GitHub%20Pages-176b87)](https://svretina.github.io/EmpiricalRelations.jl/)
[![Julia 1.10+](https://img.shields.io/badge/Julia-1.10%2B-9558B2?logo=julia)](Project.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Data: traceable CSV](https://img.shields.io/badge/data-traceable%20CSV-2b7a4b)](data/README.md)

A traceable scientific database of published empirical relations and numerical
measurements for binary-neutron-star (BNS) postmerger gravitational waves. The project
preserves the connection between normalized records and their original papers, source
tables, equations, and review status.

**[Explore the database and documentation](https://svretina.github.io/EmpiricalRelations.jl/)**
· [Waveform explorer](https://svretina.github.io/EmpiricalRelations.jl/database/explorer/)
· [Relations catalogue](https://svretina.github.io/EmpiricalRelations.jl/relations/catalogue/)

## What is included

- Reviewed waveform configurations and reported postmerger frequencies.
- Source-specific equation-of-state (EOS) properties.
- Published empirical fits with coefficients, calibration domains, and residual metrics.
- A lossless structural inventory of tables and equations across the paper corpus.
- Record-level provenance and stable source identifiers.
- A static, searchable browser interface requiring no Julia installation or backend.

The canonical research products live in [`data/`](data/README.md):

| Dataset | Purpose |
|---|---|
| [`waveforms.csv`](data/waveforms.csv) | Reviewed simulation configurations and frequency measurements |
| [`eos.csv`](data/eos.csv) | Source-specific EOS radii and maximum-mass properties |
| [`relations.csv`](data/relations/relations.csv) | Published empirical-relation catalogue |
| [`coefficients.csv`](data/relations/coefficients.csv) | Coefficients and mathematical terms for catalogued relations |
| [`sources.csv`](data/sources.csv) | Publication metadata and stable source IDs |
| [`provenance.csv`](data/provenance.csv) | Source file, table, line range, extraction method, and review state |

## Scientific conventions

Empty numeric fields mean **unavailable**, never zero. The normalized mass ratio is
`q = min(m₁,m₂)/max(m₁,m₂) ≤ 1`, while the original convention is retained separately.
Static Fourier peaks, merger frequencies, and time-dependent instantaneous frequencies
remain distinct observables.

The normative rules are documented in
[`docs/extraction_conventions.md`](docs/extraction_conventions.md); canonical frequency
definitions and paper-local aliases are in
[`docs/frequency_nomenclature.md`](docs/frequency_nomenclature.md) and
[`database/notation/paper_frequency_aliases.csv`](database/notation/paper_frequency_aliases.csv).

## Reproducibility

Regenerate and validate the public exports:

```sh
python3 scripts/extract_reference_data.py
python3 -m unittest discover -s tests -v
```

Build the documentation and interactive explorer locally:

```sh
julia --project=docs -e 'using Pkg; Pkg.develop(path="."); Pkg.instantiate()'
julia --project=docs docs/make.jl
python3 -m http.server --directory docs/build 8000
```

Then open <http://localhost:8000>. Browser JSON is generated from the canonical CSV
files during each documentation build; it is a read-only presentation layer, not a
second scientific dataset.

## Julia package status

The Julia package currently exposes the documented data catalogue. Published relations
are not advertised as callable functions until their implementations and validation
tests are added. Catalogue entries marked `catalogued` must therefore not be interpreted
as validated package models.

## Contributing and citation

See the [contribution guide](https://svretina.github.io/EmpiricalRelations.jl/contributing/)
before adding scientific records. Ambiguous notation should remain unresolved rather
than being forced into a canonical field. Cite the original publication attached to
each reused measurement or relation, as well as the repository revision or release.

EmpiricalRelations.jl is distributed under the [MIT License](LICENSE).
