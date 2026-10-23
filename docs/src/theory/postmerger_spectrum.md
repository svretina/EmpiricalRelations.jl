# Postmerger gravitational-wave spectrum

A binary neutron-star merger can leave a short-lived or longer-lived oscillating
remnant. Its gravitational radiation is nonstationary: amplitudes and characteristic
frequencies evolve while the remnant contracts, redistributes angular momentum, and
possibly collapses. A frequency measured from a finite Fourier spectrum and an
instantaneous frequency measured at a particular time are therefore not interchangeable.

## Spectral and time-dependent observables

For a complex strain mode written schematically as

```math
h_{22}(t) = A_{22}(t)e^{-i\phi_{22}(t)},
```

an instantaneous mode frequency can be defined, subject to the paper's phase-sign
convention, from the phase derivative:

```math
f_{22}(t) = \frac{1}{2\pi}\left|\frac{d\phi_{22}}{dt}\right|.
```

A spectral peak instead comes from a finite, usually windowed transform such as

```math
\tilde h(f) = \int_{t_0}^{t_1} w(t)h(t)e^{-2\pi i f t}\,dt.
```

Its location depends on the analysis interval, window, signal channel, spectral
resolution, and peak estimator. The database keeps these methodological details when
the publication reports them.

## Canonical frequency families

The database follows the physical distinctions used in the
Bauswein--Stergioulas--Vretinaris literature:

- ``f_{\mathrm{peak}}`` is the dominant postmerger Fourier-spectrum peak, generally
  associated with the remnant's quadrupolar oscillation.
- ``f_{2-0}`` is a lower-frequency sideband explicitly identified with nonlinear
  coupling between quadrupolar and quasiradial motion.
- ``f_{\mathrm{spiral}}`` is a secondary feature explicitly associated with a
  transient spiral deformation.
- ``f_0`` or `f_radial` denotes a quasiradial oscillation only when the source makes
  that physical identification.
- early, late, mean, instantaneous, and merger frequencies remain separate fields.

The coupling interpretation motivates the approximate frequency combination

```math
f_{2-0} \simeq f_{\mathrm{peak}} - f_0,
```

but this is not used to fill an unreported measurement. A directly measured sideband
and a value calculated from two other peaks have different evidential status.

## Secondary peaks and spectral classes

Published classification schemes organize spectra by the relative prominence and
physical interpretation of secondary features. Classification can depend on total
mass, EOS properties, mass ratio, and the chosen analysis procedure. The database
stores a spectral type only when the source states one explicitly; otherwise the value
is `unknown`.

Paper-local symbols such as ``f_1``, ``f_2``, or ``f_3`` are not globally unique.
In particular, a feature called ``f_1`` is not automatically mapped to
``f_{\mathrm{spiral}}`` or ``f_{2-0}``. Mappings require an explicit definition or
mode interpretation in the source and are documented in the
[frequency nomenclature](../database/frequency_nomenclature.md) and alias registry.

## Comparability limits

Before combining frequencies across publications, check at least:

- strain versus curvature or another extraction channel;
- time interval, taper, zero padding, and frequency resolution;
- coordinate, proper-time, or retarded-time convention;
- numerical method, resolution, thermal prescription, and neutrino treatment;
- whether the remnant promptly collapses or the reported interval precedes collapse;
- whether the value is a measured peak, a fitted centroid, or a model parameter.

These distinctions are why the website exposes source notes and provenance rather than
presenting all similarly named frequencies as homogeneous measurements.
