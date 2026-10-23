# Changelog

All notable user-facing changes to EmpiricalRelations.jl are recorded here. The
project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - forthcoming

### Added

- A dependency-free Julia API for discovering, selecting, evaluating, and citing 82
  reviewed BNS postmerger empirical relations.
- Calibration-domain checks, batch evaluation, stable relation identifiers, and
  source-level metadata.
- Reviewed CSV catalogues for waveforms, EOS properties, empirical relations,
  coefficients, provenance, tables, and equations from a 31-paper corpus.
- Interactive documentation for waveform data and empirical relations, including
  MathJax expressions, BibTeX export, and copyable Julia and Python implementations.
- Automated catalogue-integrity, package-quality, documentation, and explorer tests.

### Known data issues

- A source narrative reports 28 CoRe waveforms, while its numerical table contains
  27 rows; the 27 published rows are retained.
- A source narrative reports 13 CFC/SPH EOS, while its frequency table contains 12
  unique identifiers.
- SHEN and SLY4 appear in a waveform table without corresponding TOV-property rows;
  their unavailable properties remain empty.

[Unreleased]: https://github.com/svretina/EmpiricalRelations.jl/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/svretina/EmpiricalRelations.jl/releases/tag/v0.1.0
