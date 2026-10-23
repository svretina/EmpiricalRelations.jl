# EmpiricalRelations.jl

[![CI](https://github.com/svretina/EmpiricalRelations.jl/actions/workflows/CI.yml/badge.svg?branch=master)](https://github.com/svretina/EmpiricalRelations.jl/actions/workflows/CI.yml?query=branch%3Amaster)
[![Documentation](https://github.com/svretina/EmpiricalRelations.jl/actions/workflows/Documentation.yml/badge.svg?branch=master)](https://github.com/svretina/EmpiricalRelations.jl/actions/workflows/Documentation.yml?query=branch%3Amaster)
[![Documentation site](https://img.shields.io/badge/docs-GitHub%20Pages-176b87)](https://svretina.github.io/EmpiricalRelations.jl/)
[![Julia 1.10+](https://img.shields.io/badge/Julia-1.10%2B-9558B2?logo=julia)](Project.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Data: CSV](https://img.shields.io/badge/data-CSV-2b7a4b)](data/README.md)

EmpiricalRelations.jl collects published numerical measurements and empirical
relations for binary-neutron-star (BNS) postmerger gravitational waves. Normalized
records are linked to their publication, source table or equation, and review status.

**[Explore the database and documentation](https://svretina.github.io/EmpiricalRelations.jl/)**
· [Waveform explorer](https://svretina.github.io/EmpiricalRelations.jl/database/explorer/)
· [Relations catalogue](https://svretina.github.io/EmpiricalRelations.jl/relations/catalogue/)

## Data

- Reviewed waveform configurations and reported postmerger frequencies.
- Source-specific equation-of-state (EOS) properties.
- Published empirical fits with coefficients, calibration domains, and residual metrics.
- Extracted table cells and equations from the paper corpus.
- Record-level provenance and stable source identifiers.
- A searchable database browser in the documentation site.

The CSV files are stored under [`data/`](data/README.md):

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

Extraction rules are documented in
[`docs/extraction_conventions.md`](docs/extraction_conventions.md). Normalized frequency
definitions and paper-specific aliases are in
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

Then open <http://localhost:8000>. The documentation build generates the JSON files used
by the database browser from the CSV tables under `data/`.

## Julia package status

The Julia module does not yet export relation-evaluation functions. A relation has
status `catalogued` until its Julia implementation is tested against the published
expression, coefficients, units, and reference values.

## Contributing and citation

See the [contribution guide](https://svretina.github.io/EmpiricalRelations.jl/contributing/)
before adding scientific records. Mark ambiguous notation as unresolved rather than
assigning it to a normalized field. Cite the original publication for each reused
measurement or relation and record the repository revision or release.

EmpiricalRelations.jl is distributed under the [MIT License](LICENSE).
