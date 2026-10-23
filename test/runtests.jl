using EmpiricalRelations
using Test

const VRETINARIS_FPEAK_R16 = Symbol("arxiv-1910-10856-frequency-from-radius-f-peak-khz-r1-6-all-masses")
const BERNUZZI_EB = Symbol("arxiv-1504-01764-kappa2t-e-b-textmrg-2")
const LIOUTAS_R14 = Symbol("arxiv-2102-12455-fpeak-colrule-vspace0-1cm-1-2-1-2-r-3")

@testset "registry and discovery" begin
    catalogue = relations()
    @test length(catalogue) == 82
    @test length(unique(row.relation_id for row in catalogue)) == 82
    @test all(row.status === :implemented for row in catalogue)
    @test issorted(string.(getproperty.(collect(catalogue), :relation_id)))
    @test all(!occursin("f_j", formula(spec).canonical) &&
              !occursin("R_x", formula(spec).canonical) for spec in catalogue.entries)

    exact = relations(:f_peak; inputs=[:R_1_6, :M_chirp])
    @test length(exact) == 2
    @test all(Set(row.inputs) == Set((:M_chirp, :R_1_6)) for row in exact)

    available = relations(:f_peak; available=[:M_chirp, :R_1_6, :q])
    @test all(Set(row.inputs) ⊆ Set((:M_chirp, :R_1_6, :q)) for row in available)
    @test length(relations(author="Vretinaris")) == 51
    @test length(relations(publication=:Bernuzzi2015)) == 4

    @test relation(VRETINARIS_FPEAK_R16).id == RelationID(VRETINARIS_FPEAK_R16)
    @test_throws ArgumentError relation(:Vretinaris2020; quantity=:f_peak, inputs=[:M_chirp, :R_1_6])
    @test_throws ArgumentError relation(:UnknownPublication)
end

@testset "evaluation" begin
    r = relation(VRETINARIS_FPEAK_R16)
    @test evaluate(r; M_chirp=1.2, R_1_6=12.0) ≈ 3.076704 atol=1e-12
    @test evaluate(r; M_chirp=big"1.2", R_1_6=big"12.0") isa BigFloat
    @test_throws ArgumentError evaluate(r; M_chirp=1.2)
    @test_throws ArgumentError evaluate(r; M_chirp=1.2, R_1_6=12.0, q=1.0)
    @test_throws DomainError evaluate(r; M_chirp=-1.2, R_1_6=12.0)

    rows = [(M_chirp=1.2, R_1_6=12.0), (M_chirp=1.25, R_1_6=11.8)]
    @test evaluate(r, rows) == [evaluate(r; row...) for row in rows]
    @test predict(:f_peak; model=VRETINARIS_FPEAK_R16, M_chirp=1.2, R_1_6=12.0) ≈ 3.076704

    rational = relation(BERNUZZI_EB)
    expected = -0.1201 * (1 + 0.029905 * 100 + (-1.3665e-5) * 100^2) / (1 + 0.067484 * 100)
    @test evaluate(rational; kappa2T=100.0) ≈ expected

    merger = relation(Symbol("arxiv-1907-03790-eq-fpeak"))
    merger_exponent = (4.536 - 1.230 * 0.25) + (-0.929 + 3.120 * 0.25) * 400.0^(1 / 5)
    @test evaluate(merger; M_tot=2.7, eta=0.25, Lambda_tilde=400.0) ≈ 10^merger_exponent / 2.7 / 1000
    @test keys(coefficients(merger)) == (:a00, :a01, :a10, :a11)

    f1 = relation(Symbol("arxiv-2310-10728-f1-03"))
    @test_throws DomainError evaluate(f1; M_tot=2.7, q=1.1, kappa2T=100.0)
    @test_throws DomainError evaluate(merger; M_tot=2.7, eta=0.3, Lambda_tilde=400.0)

    fixed = relation(LIOUTAS_R14)
    @test evaluate(fixed; R_1_4=12.0) ≈ 10.428 - 0.8347 * 12 + 0.01749 * 12^2

    restricted = relation(Symbol("arxiv-1910-10856-radius-from-frequency-r1-2-f-peak-khz-equal-masses"))
    @test_logs (:warn, r"outside the published calibration range") evaluate(restricted; M_chirp=1.31, f_peak=3.0)
    @test_throws DomainError evaluate(restricted; M_chirp=1.31, f_peak=3.0, strict_domain=true)
end

@testset "metadata and citation" begin
    r = relation(VRETINARIS_FPEAK_R16)
    @test info(r).quantity === :f_peak
    @test info(r).output_unit === :kHz
    @test coefficients(r).b0 == 12.696
    @test occursin("f_j", formula(r).original)
    @test !occursin("f_j", formula(r).canonical)
    @test occursin("R_{1.6}", formula(r).canonical)
    @test domain(r).summary == "equal and unequal masses"
    @test source(r).arxiv_id == "1910.10856"
    @test occursin("@article{", bibtex(r))
    @test bibtex(r) == bibtex(:Vretinaris2020)
    @test_throws ArgumentError bibtex(:UnknownPublication)

    status = applicable_relations(:f_peak; M_chirp=1.2, R_1_6=12.0)
    @test !isempty(status)
    @test any(row.inputs_available for row in status)
    @test any(!row.inputs_available && row.domain_status === :missing_inputs for row in status)
end
