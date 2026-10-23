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

"""Evaluate a selected relation using canonical keyword names and units."""
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

"""Evaluate a relation for a vector of parameter `NamedTuple`s."""
evaluate(spec::RelationSpec, rows::AbstractVector{<:NamedTuple}; kwargs...) =
    [evaluate(spec; row..., kwargs...) for row in rows]

"""Resolve and evaluate one relation in a single call."""
function predict(quantity::Symbol; model, inputs=nothing, variant=nothing,
                 check_domain::Bool=true, strict_domain::Bool=false, kwargs...)
    spec = relation(Symbol(model); quantity=quantity, inputs=inputs, variant=variant)
    return evaluate(spec; check_domain=check_domain, strict_domain=strict_domain, kwargs...)
end
