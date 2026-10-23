"""List registered relations, optionally filtering by quantity, inputs, available data, author, or publication."""
function relations(quantity::Union{Nothing,Symbol}=nothing; inputs=nothing, available=nothing,
                   author=nothing, publication=nothing, implemented_only::Bool=true)
    wanted_quantity = isnothing(quantity) ? nothing : _canonical(quantity)
    exact_inputs = isnothing(inputs) ? nothing : _canonical(inputs)
    available_inputs = isnothing(available) ? nothing : Set(_canonical(available))
    entries = filter(_REGISTRY) do spec
        (isnothing(wanted_quantity) || spec.quantity === wanted_quantity) &&
        (isnothing(exact_inputs) || _canonical(spec.inputs) == exact_inputs) &&
        (isnothing(available_inputs) || Set(spec.inputs) ⊆ available_inputs) &&
        (isnothing(author) || any(contains(lowercase(name), lowercase(string(author))) for name in spec.source_info.authors)) &&
        (isnothing(publication) || spec.publication === Symbol(publication)) &&
        (!implemented_only || spec.implementation_status === :implemented)
    end
    sort!(entries; by=spec -> string(spec.id))
    return RelationCatalogue(entries)
end

function _candidates(selector::Symbol; quantity=nothing, inputs=nothing, variant=nothing)
    haskey(_BY_ID, selector) && return [_BY_ID[selector]]
    catalogue = relations(isnothing(quantity) ? nothing : Symbol(quantity);
        inputs=inputs, publication=selector, implemented_only=false)
    entries = catalogue.entries
    !isnothing(variant) && (entries = filter(spec -> spec.variant === Symbol(variant), entries))
    return entries
end

"""Retrieve exactly one relation by stable ID or by publication plus disambiguating metadata."""
function relation(selector::Union{Symbol,RelationID,AbstractString}; quantity=nothing, inputs=nothing, variant=nothing)
    key = selector isa RelationID ? Symbol(selector) : Symbol(selector)
    candidates = _candidates(key; quantity=quantity, inputs=inputs, variant=variant)
    isempty(candidates) && throw(ArgumentError("No relation matches $key. Use relations(publication=$key) to inspect available selections."))
    if length(candidates) > 1
        ids = join((string(spec.id) for spec in candidates), "\n  ")
        throw(ArgumentError("Multiple relations match $key. Specify quantity, inputs, variant, or a unique relation ID.\n  $ids"))
    end
    return only(candidates)
end

"""List models compatible with supplied values and report their known domain status."""
function applicable_relations(quantity::Symbol; kwargs...)
    available = collect(keys(kwargs))
    return [(
        relation_id=Symbol(spec.id),
        inputs_available=Set(spec.inputs) ⊆ Set(available),
        missing_inputs=Tuple(input for input in spec.inputs if !(input in available)),
        domain_status=Set(spec.inputs) ⊆ Set(available) ? _domain_status(spec, NamedTuple(kwargs)) : :missing_inputs,
    ) for spec in relations(quantity).entries]
end
