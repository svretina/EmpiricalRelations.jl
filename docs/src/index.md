# EmpiricalRelations.jl

EmpiricalRelations.jl is a traceable scientific catalogue of binary-neutron-star
postmerger gravitational-wave measurements and published empirical relations. It
connects reviewed numerical values to their original papers, source tables, and
extraction evidence without filling missing measurements or conflating incompatible
frequency definitions.

```@raw html
<div class="er-hero-links">
  <a class="er-button primary" href="database/explorer/">Explore waveform data</a>
  <a class="er-button" href="relations/catalogue/">Browse empirical relations</a>
</div>
<div id="er-summary" class="er-stat-grid" aria-live="polite"></div>
```

The project covers published numerical frequency measurements, EOS dependence,
spectral classification, and empirical or quasi-universal fits. Future package work
will build validated analytical waveform models and symbolic-regression workflows on
this evidence base.

The [canonical CSV files](database/overview.md) are the scientific source of truth.
This website is a read-only, client-side view generated from those files.

## Scientific scope

- Dominant and secondary postmerger spectral features.
- Binary masses, mass ratio, tidal deformability, EOS metadata, and simulation context.
- Published fit expressions, coefficients, applicability domains, and residuals.
- Source-level provenance for every normalized record.

Start with [frequency nomenclature](database/frequency_nomenclature.md) before
combining measurements from different publications.
