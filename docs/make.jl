using Documenter
using EmpiricalRelations

root = normpath(joinpath(@__DIR__, ".."))
run(`python3 $(joinpath(@__DIR__, "scripts", "generate_explorer_data.py"))`)

# These pages are generated from the repository's canonical documentation so that
# the website cannot drift from the extraction and nomenclature conventions. Only
# repository-relative links are adjusted for their website location.
function canonical_page(source, destination, replacements)
    content = read(source, String)
    for (old, new) in replacements
        content = replace(content, old => new)
    end
    write(destination, content)
end
canonical_page(joinpath(@__DIR__, "extraction_conventions.md"),
    joinpath(@__DIR__, "src", "database", "methodology.md"), [
        "[`database/notation/paper_frequency_aliases.csv`](../database/notation/paper_frequency_aliases.csv)" => "`database/notation/paper_frequency_aliases.csv`",
        "[`frequency_nomenclature.md`](frequency_nomenclature.md)" => "[frequency nomenclature](frequency_nomenclature.md)",
    ])
canonical_page(joinpath(@__DIR__, "frequency_nomenclature.md"),
    joinpath(@__DIR__, "src", "database", "frequency_nomenclature.md"), [
        "`database/notation/paper_frequency_aliases.csv`" => "`database/notation/paper_frequency_aliases.csv`",
        "[`extraction_conventions.md`](extraction_conventions.md)" => "[extraction methodology](methodology.md)",
    ])
canonical_page(joinpath(root, "data", "schema.md"),
    joinpath(@__DIR__, "src", "database", "schema.md"), [
        "[`docs/extraction_conventions.md`](../docs/extraction_conventions.md)" => "[extraction methodology](methodology.md)",
        "[`docs/frequency_nomenclature.md`](../docs/frequency_nomenclature.md)" => "[frequency nomenclature](frequency_nomenclature.md)",
        "[`database/notation/paper_frequency_aliases.csv`](../database/notation/paper_frequency_aliases.csv)" => "`database/notation/paper_frequency_aliases.csv`",
        "`docs/frequency_nomenclature.md`" => "the frequency-nomenclature page",
    ])

makedocs(
    modules = [EmpiricalRelations],
    sitename = "EmpiricalRelations.jl",
    authors = "Stamatis Vretinaris and contributors",
    format = Documenter.HTML(
        prettyurls = get(ENV, "CI", "false") == "true",
        canonical = "https://svretina.github.io/EmpiricalRelations.jl",
        assets = ["assets/css/database-explorer.css", "assets/js/database-explorer.js"],
        edit_link = "master",
        size_threshold = 400_000,
        mathengine = Documenter.MathJax(),
    ),
    pages = [
        "Home" => "index.md",
        "Getting started" => "getting_started.md",
        "Scientific background" => "scientific_background.md",
        "Theory" => [
            "Binary and EOS parameters" => "theory/binary_eos_parameters.md",
            "Postmerger spectrum" => "theory/postmerger_spectrum.md",
            "Empirical relations" => "theory/empirical_relations.md",
        ],
        "Database" => [
            "Overview" => "database/overview.md",
            "Interactive explorer" => "database/explorer.md",
            "Schema" => "database/schema.md",
            "Frequency nomenclature" => "database/frequency_nomenclature.md",
            "Extraction methodology" => "database/methodology.md",
            "Provenance" => "database/provenance.md",
        ],
        "Empirical relations" => [
            "Overview" => "relations/overview.md",
            "Interactive catalogue" => "relations/catalogue.md",
        ],
        "Examples" => "examples.md",
        "Julia API" => [
            "Reference" => "api.md",
            "Finding relations" => "api/finding.md",
            "Evaluating relations" => "api/evaluating.md",
            "Metadata and citations" => "api/metadata.md",
        ],
        "Citations" => "citations.md",
        "Contributing" => "contributing.md",
    ],
    warnonly = [:missing_docs],
)
