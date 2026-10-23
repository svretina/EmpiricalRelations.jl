"""Return structured scientific metadata for a relation."""
info(spec::RelationSpec) = (
    id=Symbol(spec.id), publication=spec.publication, quantity=spec.quantity,
    inputs=spec.inputs, family=spec.family, variant=spec.variant,
    output_unit=spec.output_unit, verification_status=spec.verification_status,
    implementation_status=spec.implementation_status,
)

"""Return the original and canonical mathematical expressions."""
formula(spec::RelationSpec) = (original=spec.original_equation, canonical=spec.canonical_expression)

"""Return fitted coefficients as a `NamedTuple`."""
coefficients(spec::RelationSpec) = spec.coefficient_values

"""Return applicability bounds and assumptions."""
domain(spec::RelationSpec) = (
    summary=spec.applicability.summary,
    bounds=spec.applicability.bounds,
    assumptions=copy(spec.applicability.assumptions),
)

"""Return publication and equation-level provenance."""
source(spec::RelationSpec) = spec.source_info

"""Return the source publication's BibTeX entry."""
bibtex(spec::RelationSpec) = spec.source_info.bibtex

function bibtex(publication::Symbol; quantity=nothing, inputs=nothing, variant=nothing)
    if isnothing(quantity) && isnothing(inputs) && isnothing(variant)
        haskey(_PUBLICATION_BIBTEX, publication) || throw(ArgumentError("Unknown publication $publication"))
        return _PUBLICATION_BIBTEX[publication]
    end
    return bibtex(relation(publication; quantity=quantity, inputs=inputs, variant=variant))
end
