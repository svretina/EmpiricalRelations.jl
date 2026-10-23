# Binary and EOS parameters

The inspiral and postmerger signal depend on the component masses and on how each star
responds to tidal fields. This page defines the normalized quantities used in the
database. Symbols in an original publication can follow a different ordering or mass-
ratio convention; the original value and definition remain available alongside the
normalized fields.

## Mass variables

For gravitational masses ``m_1`` and ``m_2``, the total mass is

```math
M_{\mathrm{tot}} = m_1 + m_2,
```

and the chirp mass is

```math
\mathcal{M} = \frac{(m_1m_2)^{3/5}}{(m_1+m_2)^{1/5}}.
```

The public field `q` always uses the bounded convention

```math
q = \frac{\min(m_1,m_2)}{\max(m_1,m_2)} \leq 1.
```

Some papers instead use the reciprocal ratio or impose a fixed label ordering. Those
values are not discarded: `q_original` and `q_original_definition` preserve them.
Equal-mass filtering in the explorer refers to the normalized value ``q=1``.

## Tidal deformability

The dimensionless quadrupolar tidal deformability of component ``A`` is commonly
written

```math
\Lambda_A = \frac{2}{3} k_2^{(A)}
             \left(\frac{c^2 R_A}{Gm_A}\right)^5,
```

where ``k_2`` is the quadrupolar Love number and ``R_A`` is the stellar radius. The
binary effective tidal deformability used in inspiral analyses is

```math
\tilde{\Lambda} = \frac{16}{13}
\frac{(m_1+12m_2)m_1^4\Lambda_1 +
      (m_2+12m_1)m_2^4\Lambda_2}
     {(m_1+m_2)^5}.
```

The database stores source-reported ``\Lambda_1``, ``\Lambda_2``, and
``\tilde{\Lambda}`` where available. It does not infer a missing tidal parameter from
an EOS label or an empirical frequency fit.

## EOS properties

An equation of state relates thermodynamic variables and determines the sequence of
cold, nonrotating stellar models. Radius fields such as `r_1_6_km` refer to the radius
of a cold star with the indicated mass; they are not radii of the hot merger remnant.
`m_tov_msun` denotes a source-reported maximum mass for a nonrotating sequence when the
publication supplies one.

EOS rows are source-specific. Values with the same nominal EOS name are not averaged
across papers because differences in EOS variants, thermal treatment, or tabulation can
be scientifically relevant. Consult the row's source and definition notes before
joining EOS properties to waveform measurements.

## Derived versus reported quantities

Total mass, chirp mass, or normalized mass ratio may be calculated algebraically from
reported component masses when the source convention is explicit. Such deterministic
derivations are different from empirical predictions: they introduce no fitted
physics, but remain subject to rounding in the published inputs. The extraction notes
record when a value was derived rather than transcribed.
