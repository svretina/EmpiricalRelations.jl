# Database overview

The database contains waveform frequencies, source-specific EOS properties,
publication metadata, extraction provenance, and empirical relations. The counts and
checksum below are computed during the documentation build.

```@raw html
<div id="er-database-summary" class="er-stat-grid" aria-live="polite"></div>
```

## Files and versioning

The published tables are the CSV files under `data/`. The documentation build validates
their columns and foreign keys, then writes JSON for the database explorer. Empty CSV
fields are represented by JSON `null`. Numerical text in the downloadable CSV files is
not rewritten by the web interface.

Masses use solar masses, normalized postmerger frequencies use kHz, radii use km, and
the initial GW-frequency field uses Hz. The normalized mass ratio is
`min(m1,m2)/max(m1,m2) ≤ 1`.

## Missing values and uncertainty

An empty numeric CSV cell denotes missing data. Companion status fields distinguish
unreported and unidentified secondary peaks where the publication supports that
distinction. Published uncertainty notation is retained in the extracted source cell.
Notes record the measurement channel, window, numerical method, and stated limitations
when available.

Field definitions are listed in the [schema](schema.md). The
[extraction methodology](methodology.md) and [provenance fields](provenance.md) describe
how records can be checked against the publications.
