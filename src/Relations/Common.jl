# Explicit numerical implementations shared by relations with the same published form.

function _frequency_from_radius(c, M_chirp, radius)
    polynomial = c.b0 + c.b1 * M_chirp + c.b2 * radius + c.b3 * M_chirp^2 +
                 c.b4 * radius * M_chirp + c.b5 * radius^2
    return M_chirp * polynomial
end


function _radius_from_frequency(c, M_chirp, frequency)
    ratio = frequency / M_chirp
    return c.b0 + c.b1 * M_chirp + c.b2 * ratio + c.b3 * M_chirp^2 +
           c.b4 * frequency + c.b5 * ratio^2
end


_frequency_from_tidal(c, M_chirp, Lambda_tilde) =
    (c.b0 + c.b1 * M_chirp + c.b2 * inv(sqrt(Lambda_tilde))) / M_chirp

_tidal_rational(c, kappa2T) =
    c.Q0 * (1 + c.n1 * kappa2T + c.n2 * kappa2T^2) / (1 + c.d1 * kappa2T)

function _eta_tidal_frequency(c, M_tot, eta, Lambda_tilde)
    c00, c01, c10, c11 = if hasproperty(c, :c00)
        (c.c00, c.c01, c.c10, c.c11)
    else
        (c.a00, c.a01, c.a10, c.a11)
    end
    exponent = (c00 + c01 * eta) + (c10 + c11 * eta) * Lambda_tilde^(1 / 5)
    return 10^exponent / M_tot / 1000
end


function _mass_ratio_tidal_frequency(c, M_tot, q, kappa2T)
    exponent = c.a0 + (c.b0 + c.b1 * q + c.b2 * q^2) * kappa2T^c.n
    return 10^exponent / M_tot / 1000
end

_fixed_mass_peak(c, value) = c.b0 + c.b1 * value + c.b2 * value^2

function _evaluator(family::Symbol, coefficients::NamedTuple)
    family === :frequency_from_radius && return (args...) -> _frequency_from_radius(coefficients, args...)
    family === :radius_from_frequency && return (args...) -> _radius_from_frequency(coefficients, args...)
    family in (:frequency_from_tidal_deformability, :secondary_frequency_from_tidal_deformability,
               :spiral_frequency_from_tidal_deformability) && return (args...) -> _frequency_from_tidal(coefficients, args...)
    family === :tidal_coupling_rational_fit && return (args...) -> _tidal_rational(coefficients, args...)
    family in (:merger_frequency_from_tidal_deformability, :postmerger_frequency_from_tidal_deformability) &&
        return (args...) -> _eta_tidal_frequency(coefficients, args...)
    family === :F1_tidal_mass_ratio_frequency_fit && return (args...) -> _mass_ratio_tidal_frequency(coefficients, args...)
    family === :fixed_mass_peak_frequency && return (args...) -> _fixed_mass_peak(coefficients, args...)
    error("No evaluator registered for relation family $family")
end
