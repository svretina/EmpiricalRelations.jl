const _REGISTRY = RelationSpec[]
const _BY_ID = Dict{Symbol,RelationSpec}()
const _PUBLICATION_BIBTEX = Dict{Symbol,String}()

function _register!(spec::RelationSpec)
    haskey(_BY_ID, Symbol(spec.id)) && error("duplicate relation ID $(spec.id)")
    push!(_REGISTRY, spec)
    _BY_ID[Symbol(spec.id)] = spec
    _PUBLICATION_BIBTEX[spec.publication] = spec.source_info.bibtex
    return spec
end

function _validate_registry()
    length(_REGISTRY) == length(_BY_ID) || error("relation registry contains duplicate IDs")
    for spec in _REGISTRY
        isempty(spec.inputs) && error("$(spec.id) has no required inputs")
        spec.publication == spec.source_info.publication || error("$(spec.id) has inconsistent publication metadata")
        spec.implementation_status === :implemented || error("$(spec.id) has no verified evaluator")
        startswith(string(spec.verification_status), "verified_") ||
            error("$(spec.id) has not passed scientific review")
        isempty(spec.source_info.bibtex) && error("$(spec.id) has no publication citation")
    end
    return nothing
end

const _ALIASES = Dict(
    :f_peak_khz => :f_peak, :f_peak_hz => :f_peak,
    :f_2_0_khz => :f_2_0, :f_spiral_khz => :f_spiral,
    :f_merger_hz => :f_merger, :f_merger_khz => :f_merger,
    :mchirp_msun => :M_chirp, :mtot_msun => :M_tot, :total_mass_msun => :M_tot,
    :lambda_tilde => :Lambda_tilde, :kappa_2_T => :kappa2T,
    :r_1_2_km => :R_1_2, :r_1_4_km => :R_1_4, :r_1_6_km => :R_1_6, :r_1_8_km => :R_1_8,
)

_canonical(value::Symbol) = get(_ALIASES, value, value)
_canonical(values) = Tuple(sort!([_canonical(Symbol(value)) for value in values]; by=string))
