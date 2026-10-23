"""
    relations([quantity]; inputs=nothing, available=nothing, author=nothing,
              publication=nothing, implemented_only=true)

Return a [`RelationCatalogue`](@ref) of registered empirical relations.

`inputs` matches the exact required input set, independent of order. `available`
instead keeps relations whose required inputs are a subset of the supplied variables.
Filter by a case-insensitive author substring or an exact publication symbol. Callable
relations are returned by default.

# Examples
```julia
relations(:f_peak)
relations(:f_peak; inputs=[:M_chirp, :Lambda_tilde])
relations(:f_peak; available=[:M_chirp, :Lambda_tilde, :q])
relations(author="Vretinaris")
```
"""
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

"""
    relation(selector; quantity=nothing, inputs=nothing, variant=nothing)

Retrieve exactly one [`RelationSpec`](@ref). `selector` may be a stable relation ID or
a publication symbol. Publication selection may be narrowed by output `quantity`, exact
`inputs`, and `variant`.

An ambiguous selection raises `ArgumentError` and lists candidate stable IDs; no model
is selected implicitly.
"""
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

"""
    applicable_relations(quantity; values...)

Report input availability and known numerical-domain status for every implemented
relation predicting `quantity`.

Rows contain `relation_id`, `inputs_available`, `missing_inputs`, and `domain_status`.
The status is `:within`, `:outside`, `:unknown`, or `:missing_inputs`. Categorical
assumptions are not inferred from numerical keywords; inspect [`domain`](@ref) as well.
"""
function applicable_relations(quantity::Symbol; kwargs...)
    available = collect(keys(kwargs))
    return [(
        relation_id=Symbol(spec.id),
        inputs_available=Set(spec.inputs) ⊆ Set(available),
        missing_inputs=Tuple(input for input in spec.inputs if !(input in available)),
        domain_status=Set(spec.inputs) ⊆ Set(available) ? _domain_status(spec, NamedTuple(kwargs)) : :missing_inputs,
    ) for spec in relations(quantity).entries]
end
