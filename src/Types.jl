"""Stable, globally unique identifier for one empirical relation."""
struct RelationID
    value::Symbol
end

RelationID(value::AbstractString) = RelationID(Symbol(value))
Base.Symbol(id::RelationID) = id.value
Base.string(id::RelationID) = string(id.value)
Base.show(io::IO, id::RelationID) = print(io, id.value)

"""Scientific source metadata for a published relation."""
struct SourceInfo
    publication::Symbol
    source_id::String
    title::String
    authors::Vector{String}
    year::Int
    doi::Union{Nothing,String}
    arxiv_id::String
    url::String
    equation_label::String
    source_table::String
    source_path::String
    bibtex::String
end

"""Applicability metadata. Unknown bounds are represented by an empty `bounds` tuple."""
struct DomainSpec
    summary::String
    bounds::NamedTuple
    assumptions::Vector{String}
end

"""One published empirical relation and its explicitly registered evaluator."""
struct RelationSpec
    id::RelationID
    publication::Symbol
    quantity::Symbol
    inputs::Tuple{Vararg{Symbol}}
    family::Symbol
    variant::Symbol
    original_equation::String
    canonical_expression::String
    coefficient_values::NamedTuple
    output_unit::Symbol
    applicability::DomainSpec
    source_info::SourceInfo
    verification_status::Symbol
    implementation_status::Symbol
    evaluator::Function
end

function Base.show(io::IO, relation::RelationSpec)
    print(io, "RelationSpec(", relation.id, ", ", relation.quantity, "(")
    join(io, relation.inputs, ", ")
    print(io, "), ", relation.publication, ", ", relation.output_unit, ")")
end

"""A lightweight, tabular view returned by [`relations`](@ref)."""
struct RelationCatalogue <: AbstractVector{NamedTuple}
    entries::Vector{RelationSpec}
end

Base.size(catalogue::RelationCatalogue) = (length(catalogue.entries),)
Base.length(catalogue::RelationCatalogue) = length(catalogue.entries)
Base.IndexStyle(::Type{RelationCatalogue}) = IndexLinear()
function Base.getindex(catalogue::RelationCatalogue, index::Int)
    relation = catalogue.entries[index]
    return (
        relation_id = Symbol(relation.id),
        publication = relation.publication,
        quantity = relation.quantity,
        inputs = relation.inputs,
        validity = relation.applicability.summary,
        status = relation.implementation_status,
    )
end

function Base.show(io::IO, ::MIME"text/plain", catalogue::RelationCatalogue)
    println(io, length(catalogue), " empirical relation", length(catalogue) == 1 ? "" : "s")
    for row in catalogue
        println(io, "  ", row.relation_id, "  ", row.quantity, row.inputs, "  ", row.publication, "  ", row.status)
    end
end
