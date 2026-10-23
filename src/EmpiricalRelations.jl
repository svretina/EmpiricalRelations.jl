module EmpiricalRelations

export RelationID, RelationSpec, RelationCatalogue
export relations, relation, evaluate, predict, applicable_relations
export info, formula, coefficients, domain, source, bibtex

include("Types.jl")
include("Relations/Common.jl")
include("Registry.jl")
include("GeneratedRegistry.jl")
include("Discovery.jl")
include("Evaluation.jl")
include("Metadata.jl")

function __init__()
    _validate_registry()
end

end
