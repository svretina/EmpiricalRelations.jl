function _numeric_checks(spec::RelationSpec, values::NamedTuple)
    for (name, value) in pairs(values)
        value isa Real || throw(ArgumentError("$name must be a real number"))
        isfinite(value) || throw(DomainError(value, "$name must be finite"))
        label = string(name)
        if (name in (:M_chirp, :M_tot, :Lambda_tilde, :kappa2T) ||
            startswith(label, "R_") || startswith(label, "Lambda_") ||
            startswith(label, "f_")) && value <= zero(value)
            throw(DomainError(value, "$name must be positive"))
        end
        name === :q && !(zero(value) < value <= one(value)) &&
            throw(DomainError(value, "q must follow the canonical convention 0 < q ≤ 1"))
        name === :eta && !(zero(value) < value <= one(value) / 4) &&
            throw(DomainError(value, "eta must satisfy 0 < eta ≤ 1/4"))
    end
    return nothing
end

function _domain_status(spec::RelationSpec, values::NamedTuple)
    isempty(keys(spec.applicability.bounds)) && return :unknown
    for (name, interval) in pairs(spec.applicability.bounds)
        haskey(values, name) || continue
        minimum, maximum = interval
        minimum !== nothing && values[name] < minimum && return :outside
        maximum !== nothing && values[name] > maximum && return :outside
    end
    return :within
end

"""
    evaluate(spec::RelationSpec; check_domain=true, strict_domain=false, inputs...)

Evaluate a selected empirical relation using its canonical keyword names. Frequencies
are returned in kHz, radii in km, and dimensionless observables without a unit.

Missing, unexpected, non-real, non-finite, and physically invalid inputs raise an
error. A known calibration-domain violation warns by default. Set `strict_domain=true`
to raise `DomainError`, or `check_domain=false` for an intentional extrapolation. Inputs
are never clipped.

Use `info(spec).inputs` and `info(spec).output_unit` to inspect the required signature
and output unit.
"""
function evaluate(spec::RelationSpec; check_domain::Bool=true, strict_domain::Bool=false, kwargs...)
    supplied = NamedTuple(kwargs)
    missing = filter(name -> !haskey(supplied, name), spec.inputs)
    isempty(missing) || throw(ArgumentError("Relation requires: $(join(spec.inputs, ", ")). Missing: $(join(missing, ", "))."))
    extras = filter(name -> !(name in spec.inputs), keys(supplied))
    isempty(extras) || throw(ArgumentError("Unexpected inputs for $(spec.id): $(join(extras, ", "))"))
    ordered = NamedTuple{spec.inputs}(Tuple(supplied[name] for name in spec.inputs))
    _numeric_checks(spec, ordered)
    if check_domain
        status = _domain_status(spec, ordered)
        if status === :outside
            message = "Input lies outside the published calibration range for $(spec.id)."
            strict_domain ? throw(DomainError(ordered, message)) : @warn message
        end
    end
    result = spec.evaluator((ordered[name] for name in spec.inputs)...)
    result isa Real && isfinite(result) ||
        throw(DomainError(result, "Relation $(spec.id) produced a non-finite result"))
    return result
end

"""
    evaluate(spec::RelationSpec, rows::AbstractVector{<:NamedTuple}; kwargs...)

Evaluate `spec` for each named tuple in `rows`, applying the scalar input and domain
validation to every row. Additional keywords such as `strict_domain=true` are forwarded
to scalar [`evaluate`](@ref).
"""
evaluate(spec::RelationSpec, rows::AbstractVector{<:NamedTuple}; kwargs...) =
    [evaluate(spec; row..., kwargs...) for row in rows]

"""
    predict(quantity; model, inputs=nothing, variant=nothing,
            check_domain=true, strict_domain=false, values...)

Resolve one model and evaluate it in a single call. `model` is a publication selector
or stable relation ID; `inputs` describes the desired model signature, while the
remaining keywords are physical values. Numerical work is delegated to [`evaluate`](@ref).
"""
function predict(quantity::Symbol; model, inputs=nothing, variant=nothing,
                 check_domain::Bool=true, strict_domain::Bool=false, kwargs...)
    spec = relation(Symbol(model); quantity=quantity, inputs=inputs, variant=variant)
    return evaluate(spec; check_domain=check_domain, strict_domain=strict_domain, kwargs...)
end
