# Database overview

The public database contains normalized waveform configurations, source-specific EOS
properties, publication metadata, provenance, and reviewed empirical relations. Its
current size and data fingerprint are shown below.

```@raw html
<div id="er-database-summary" class="er-stat-grid" aria-live="polite"></div>
```

## Authority and versioning

The files under `data/` are authoritative. Browser JSON is regenerated during every
documentation build, validated against required columns and foreign keys, and contains
JSON `null` for missing values. The site does not impute data or alter precision in the
canonical downloads.

Masses use solar masses, normalized postmerger frequencies use kHz, radii use km, and
the initial GW-frequency field uses Hz. The normalized mass ratio is
`min(m1,m2)/max(m1,m2) ≤ 1`.

## Missing values and uncertainty

An empty numeric CSV cell is missing, not zero. Companion status fields describe
unreported or unidentified secondary peaks when the source permits. Published
uncertainties remain in source cells and provenance; no generic uncertainty is
invented. Measurement channel, windowing, numerical method, and other limitations are
retained in notes where available.

Use the [schema](schema.md), [methodology](methodology.md), and [provenance guide](provenance.md)
before statistical reuse.
