# EmpiricalRelations.jl

```@raw html
<div class="er-project-logo">
  <img src="assets/images/logo.png" alt="EmpiricalRelations.jl — binary neutron-star merger and gravitational-wave logo">
</div>
```

EmpiricalRelations.jl collects published numerical measurements and empirical
relations for binary-neutron-star postmerger gravitational waves. Each normalized
record includes a publication identifier and the location of the source table or
equation from which it was extracted.

```@raw html
<div class="er-hero-links">
  <a class="er-button primary" href="api/finding/">Use the Julia API</a>
  <a class="er-button primary" href="database/explorer/">Explore waveform data</a>
  <a class="er-button" href="relations/catalogue/">Browse empirical relations</a>
</div>
<div id="er-summary" class="er-stat-grid" aria-live="polite"></div>
```

The collection includes postmerger frequencies, binary and EOS parameters, spectral
classifications, and published fit coefficients. Data are distributed as CSV files in
the repository. The documentation build converts these tables to JSON for the search
interface.

## Scientific scope

- Dominant and secondary postmerger spectral features.
- Binary masses, mass ratio, tidal deformability, EOS metadata, and simulation context.
- Published fit expressions, coefficients, applicability domains, and residuals.
- Source-level provenance for every normalized record.

## Julia API

Published relations can be discovered, evaluated, inspected, and cited without loading
the waveform database:

```julia
using EmpiricalRelations

r = relation(:Vretinaris2026;
    quantity=:f_2_0,
    inputs=[:M_chirp, :Lambda_tilde],
)

evaluate(r; M_chirp=1.2, Lambda_tilde=500.0)
bibtex(r)
```

See [getting started](getting_started.md) and the [API guide](api/finding.md).

Consult the [frequency nomenclature](database/frequency_nomenclature.md) when comparing
measurements from different publications.
