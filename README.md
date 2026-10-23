# EmpiricalRelations.jl

<p align="center">
  <img src="docs/src/assets/images/logo.png" alt="EmpiricalRelations.jl — binary neutron-star merger and gravitational-wave logo" width="720">
</p>

[![CI](https://github.com/svretina/EmpiricalRelations.jl/actions/workflows/CI.yml/badge.svg?branch=master)](https://github.com/svretina/EmpiricalRelations.jl/actions/workflows/CI.yml?query=branch%3Amaster)
[![GitHub release](https://img.shields.io/github/v/release/svretina/EmpiricalRelations.jl)](https://github.com/svretina/EmpiricalRelations.jl/releases/latest)
[![Aqua QA](https://juliatesting.github.io/Aqua.jl/dev/assets/badge.svg)](https://github.com/JuliaTesting/Aqua.jl)
[![Documentation](https://github.com/svretina/EmpiricalRelations.jl/actions/workflows/Documentation.yml/badge.svg?branch=master)](https://github.com/svretina/EmpiricalRelations.jl/actions/workflows/Documentation.yml?query=branch%3Amaster)
[![Documentation site](https://img.shields.io/badge/docs-GitHub%20Pages-176b87)](https://svretina.github.io/EmpiricalRelations.jl/)
[![Julia 1.10+](https://img.shields.io/badge/Julia-1.10%2B-9558B2?logo=julia)](Project.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Data: CSV](https://img.shields.io/badge/data-CSV-2b7a4b)](data/README.md)

EmpiricalRelations.jl collects published numerical measurements and empirical
relations for binary-neutron-star (BNS) postmerger gravitational waves. Normalized
records are linked to their publication, source table or equation, and review status.
The Julia API provides searchable, citable implementations of the reviewed relations.

**[Explore the database and documentation](https://svretina.github.io/EmpiricalRelations.jl/)**
· [Waveform explorer](https://svretina.github.io/EmpiricalRelations.jl/database/explorer/)
· [Relations catalogue](https://svretina.github.io/EmpiricalRelations.jl/relations/catalogue/)
· [API guide](https://svretina.github.io/EmpiricalRelations.jl/api/finding/)

## Installation

```julia
using Pkg
Pkg.add(url="https://github.com/svretina/EmpiricalRelations.jl")
```

EmpiricalRelations.jl has no runtime dependencies beyond the Julia standard library.
The API does not load the waveform tables or literature-processing pipeline.

## Quick start

The main workflow is discover, select, evaluate, and cite:

```julia
using EmpiricalRelations

# Find fits for the dominant postmerger frequency.
relations(:f_peak; inputs=[:M_tot, :eta, :Lambda_tilde])

# Publication + observable + inputs uniquely identify this relation.
r = relation(:Kiuchi2020;
    quantity=:f_peak,
    inputs=[:M_tot, :eta, :Lambda_tilde],
)

f_peak = evaluate(r; M_tot=2.7, eta=0.25, Lambda_tilde=400.0) # kHz

formula(r)       # original and canonical LaTeX
coefficients(r)  # fitted coefficients
domain(r)        # calibration bounds and assumptions
source(r)        # paper and equation provenance
bibtex(r)        # citation for the original relation
```

Use a stable relation ID when a publication contains multiple fits with the same
observable and inputs. The package reports ambiguity instead of choosing a calibration
population implicitly.

### Batch evaluation

```julia
systems = [
    (M_tot=2.65, eta=0.250, Lambda_tilde=500.0),
    (M_tot=2.80, eta=0.245, Lambda_tilde=350.0),
]

frequencies_khz = evaluate(r, systems)
```

### Compare published models

```julia
models = relations(:f_merger; inputs=[:M_tot, :q, :kappa2T])
predictions = [
    (publication=row.publication,
     relation_id=row.relation_id,
     f_merger_khz=evaluate(relation(row.relation_id);
                           M_tot=2.7, q=0.9, kappa2T=100.0))
    for row in models
]
```

See the [research workflows](https://svretina.github.io/EmpiricalRelations.jl/api/workflows/)
for model comparison, applicability checks, batch calculations, and citation export.

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
python3 scripts/generate_julia_registry.py
python3 -m unittest discover -s tests -v
julia --project=. -e 'using Pkg; Pkg.test()'
```

Build the documentation and interactive explorer locally:

```sh
julia --project=docs -e 'using Pkg; Pkg.develop(path="."); Pkg.instantiate()'
julia --project=docs docs/make.jl
python3 -m http.server --directory docs/build 8000
```

Then open <http://localhost:8000>. The documentation build generates the JSON files used
by the database browser from the CSV tables under `data/`.

## Units and validity

Frequencies use kHz, masses use solar masses, radii use km, and tidal parameters are
dimensionless. Mathematical input checks are always applied. Known empirical-domain
violations warn by default and can be made errors with `strict_domain=true`. An unknown
domain is retained as unknown rather than treated as unrestricted validity. See
[units and symbols](https://svretina.github.io/EmpiricalRelations.jl/api/conventions/).

## Contributing and citation

See the [contribution guide](https://svretina.github.io/EmpiricalRelations.jl/contributing/)
before adding scientific records. Mark ambiguous notation as unresolved rather than
assigning it to a normalized field. Cite the original publication for each reused
measurement or relation and record the repository revision or release.

Release-level citation metadata are provided in [`CITATION.cff`](CITATION.cff).
`bibtex(r)` returns the original publication that introduced a selected empirical
relation; cite both that publication and the software release used in an analysis.
The scope of the software license and third-party scientific material is described in
[`DATA_NOTICE.md`](DATA_NOTICE.md).

EmpiricalRelations.jl is distributed under the [MIT License](LICENSE).
