"""
    info(spec)

Return a named tuple containing the stable ID, publication, predicted quantity, required
inputs, fit family, variant, canonical output unit, verification status, and
implementation status.
"""
info(spec::RelationSpec) = (
    id=Symbol(spec.id), publication=spec.publication, quantity=spec.quantity,
    inputs=spec.inputs, family=spec.family, variant=spec.variant,
    output_unit=spec.output_unit, verification_status=spec.verification_status,
    implementation_status=spec.implementation_status,
)

"""
    formula(spec)

Return `(original, canonical)` LaTeX strings. `original` preserves the transcribed
publication expression; `canonical` specializes generic family placeholders to this
relation's observable and inputs. Evaluation never parses these strings.
"""
formula(spec::RelationSpec) = (original=spec.original_equation, canonical=spec.canonical_expression)

"""
    coefficients(spec)

Return fitted coefficient names and numerical values as a `NamedTuple`, retaining the
coefficient symbols used by the publication.
"""
coefficients(spec::RelationSpec) = spec.coefficient_values

"""
    domain(spec)

Return `(summary, bounds, assumptions)` for the relation's reported applicability.
`bounds` contains only machine-checkable numerical limits. Empty bounds mean that no
limits are encoded, not that the relation is valid without restriction.
"""
domain(spec::RelationSpec) = (
    summary=spec.applicability.summary,
    bounds=spec.applicability.bounds,
    assumptions=copy(spec.applicability.assumptions),
)

"""
    source(spec)

Return [`SourceInfo`](@ref) with publication metadata, DOI and arXiv identifiers,
equation or table references, extraction path, and BibTeX entry.
"""
source(spec::RelationSpec) = spec.source_info

"""
    bibtex(spec)
    bibtex(publication; quantity=nothing, inputs=nothing, variant=nothing)

Return the original source publication's BibTeX entry. A publication symbol can be
used directly because all relations from that publication share the citation. Supply
relation selectors when resolving a specific fit is also desired.
"""
bibtex(spec::RelationSpec) = spec.source_info.bibtex

function bibtex(publication::Symbol; quantity=nothing, inputs=nothing, variant=nothing)
    if isnothing(quantity) && isnothing(inputs) && isnothing(variant)
        haskey(_PUBLICATION_BIBTEX, publication) || throw(ArgumentError("Unknown publication $publication"))
        return _PUBLICATION_BIBTEX[publication]
    end
    return bibtex(relation(publication; quantity=quantity, inputs=inputs, variant=variant))
end
