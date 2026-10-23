#!/usr/bin/env python3
"""Generate the dependency-free Julia registry from reviewed canonical CSV data."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def julia_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False).replace("$", "\\$")


def symbol(value: str) -> str:
    return f"Symbol({julia_string(value)})"


def bibtex_entries() -> dict[str, str]:
    content = (ROOT / "papers" / "bibliography.bib").read_text()
    result = {}
    for entry in re.findall(r"(?ms)^@\w+\{.*?^\}\s*$", content):
        match = re.search(r"(?m)^\s*eprint\s*=\s*\{([^}]+)\}", entry)
        if match:
            result[match.group(1)] = entry.strip()
    return result


def number(token: str) -> float:
    token = re.sub(r"\s+", "", token)
    token = re.sub(r"\\times10\^\{([+-]?\d+)\}", r"e\1", token)
    return float(token)


def fixed_coefficients(equation: str) -> dict[str, float]:
    rhs = equation.strip().strip("$").split("=", 1)[1]
    numeric = r"[+-]?\s*\d+(?:\.\d+)?(?:\s*\\times\s*10\^\{[+-]?\d+\})?"
    constant = re.match(rf"\s*({numeric})", rhs)
    terms = re.findall(rf"({numeric})\s*(?=(?:\\left\s*\()?\s*(?:R_|\\Lambda))", rhs)
    if constant is None or len(terms) != 2:
        raise ValueError(f"cannot parse fixed-mass fit: {equation}")
    return {"b0": number(constant.group(1)), "b1": number(terms[0]), "b2": number(terms[1])}


def publication_id(source: dict) -> str:
    first = source["authors"].split(";")[0]
    surname = re.sub(r"[^A-Za-z]", "", first.split()[-1])
    return f"{surname}{source['publication_year']}"


def quantity(row: dict) -> str:
    value = row["dependent_variable"]
    direct = {
        "f_peak_khz": "f_peak", "f_peak_hz": "f_peak",
        "f_peak_khz*mchirp_msun": "f_peak",
        "f_2_0_khz": "f_2_0", "f_spiral_khz": "f_spiral",
        "f_merger_hz": "f_merger", "f_peak_instantaneous_hz": "f_peak_instantaneous",
        "E_b^\\textmrg": "E_b_mrg", "j^\\textmrg": "j_mrg",
        "M\\omega_22^\\textmrg": "Momega_22_mrg", "Mf_2": "Mf_2",
    }
    if value in direct:
        return direct[value]
    radius = re.fullmatch(r"r_1_([2468])_km", value)
    if radius:
        return f"R_1_{radius.group(1)}"
    raise ValueError(f"unknown dependent variable {value}")


def fixed_input(equation: str) -> str:
    radius = re.search(r"R_\{([0-9.]+)\}(?:\^\{(90\\%|\\mathrm\{cc\})\})?", equation)
    if radius:
        mass = radius.group(1).replace(".", "_")
        suffix = "_90" if radius.group(2) == "90\\%" else "_cc" if radius.group(2) else ""
        return f"R_{mass}{suffix}"
    tidal = re.search(r"\\Lambda\^\{1/5\}_\{([0-9.]+)\}", equation)
    if tidal:
        return f"Lambda_{tidal.group(1).replace('.', '_')}_one_fifth"
    raise ValueError(f"unknown fixed-mass input in {equation}")


def inputs(row: dict) -> tuple[str, ...]:
    if row["family"] == "fixed_mass_peak_frequency":
        return (fixed_input(row["equation_latex"]),)
    if row["family"] in {
        "merger_frequency_from_tidal_deformability",
        "postmerger_frequency_from_tidal_deformability",
    }:
        # The published evaluator is defined as f(M_tot, eta, Lambda_tilde),
        # independently of the column order used by the literature inventory.
        return ("M_tot", "eta", "Lambda_tilde")
    mapping = {
        "mchirp_msun": "M_chirp", "total_mass_msun": "M_tot",
        "q": "q", "eta": "eta", "lambda_tilde": "Lambda_tilde",
        "lambda_tilde^(-1/2)": "Lambda_tilde", "lambda_tilde^(1/5)": "Lambda_tilde",
        "kappa_2_T": "kappa2T", "r_1_2_km": "R_1_2", "r_1_4_km": "R_1_4",
        "r_1_6_km": "R_1_6", "r_1_8_km": "R_1_8",
        "f_peak_khz": "f_peak", "f_2_0_khz": "f_2_0", "f_spiral_khz": "f_spiral",
    }
    return tuple(mapping[value] for value in row["independent_variables"].split(";"))


def canonical_expression(row: dict) -> str:
    """Specialize placeholders in a published family expression for one relation."""
    expression = row["equation_latex"]
    quantity_latex = {
        "f_peak_khz": r"f_{\mathrm{peak}}",
        "f_peak_hz": r"f_{\mathrm{peak}}",
        "f_peak_khz*mchirp_msun": r"f_{\mathrm{peak}}",
        "f_2_0_khz": r"f_{2-0}",
        "f_spiral_khz": r"f_{\mathrm{spiral}}",
        "f_merger_hz": r"f_{\mathrm{mrg}}",
        "f_peak_instantaneous_hz": r"f_{\mathrm{peak}}^{\mathrm{inst}}",
        r"E_b^\textmrg": r"E_b^{\mathrm{mrg}}",
        r"j^\textmrg": r"j^{\mathrm{mrg}}",
        r"M\omega_22^\textmrg": r"M\omega_{22}^{\mathrm{mrg}}",
        "Mf_2": r"M f_2",
    }
    input_latex = {
        "f_peak_khz": r"f_{\mathrm{peak}}",
        "f_2_0_khz": r"f_{2-0}",
        "f_spiral_khz": r"f_{\mathrm{spiral}}",
        "r_1_2_km": r"R_{1.2}",
        "r_1_4_km": r"R_{1.4}",
        "r_1_6_km": r"R_{1.6}",
        "r_1_8_km": r"R_{1.8}",
    }
    raw_inputs = row["independent_variables"].split(";")
    frequency = quantity_latex.get(row["dependent_variable"])
    if not row["dependent_variable"].startswith("f_"):
        frequency = next((input_latex[value] for value in raw_inputs if value.startswith("f_")), None)
    radius = input_latex.get(row["dependent_variable"])
    if not row["dependent_variable"].startswith("r_"):
        radius = next((input_latex[value] for value in raw_inputs if value.startswith("r_")), None)
    if frequency:
        expression = re.sub(r"\bf_j\b", lambda _: frequency, expression)
    if radius:
        expression = re.sub(r"\bR_x\b", lambda _: radius, expression)
    if row["family"] == "tidal_coupling_rational_fit":
        expression = re.sub(r"^Q(?=\s*\()", lambda _: quantity_latex[row["dependent_variable"]], expression)
    if row["family"] == "F1_tidal_mass_ratio_frequency_fit":
        expression = re.sub(r"\bf(?=/Hz)", lambda _: quantity_latex[row["dependent_variable"]], expression)
    return expression


def domain(row: dict) -> tuple[str, list[str]]:
    app = row["applicability"]
    if "M_chirp < 1.3" in app:
        return "(; M_chirp = (nothing, 1.3))", [part.strip() for part in app.split(";")[1:]]
    if "M_chirp > 1.3" in app:
        return "(; M_chirp = (1.3, nothing))", [part.strip() for part in app.split(";")[1:]]
    return "NamedTuple()", [part.strip() for part in app.split(";") if part.strip()]


def generated_content() -> tuple[str, int]:
    with (ROOT / "data" / "relations" / "relations.csv").open(newline="") as handle:
        relations = list(csv.DictReader(handle))
    with (ROOT / "data" / "relations" / "coefficients.csv").open(newline="") as handle:
        coefficient_rows = list(csv.DictReader(handle))
    with (ROOT / "data" / "sources.csv").open(newline="") as handle:
        sources = {row["source_id"]: row for row in csv.DictReader(handle)}

    grouped = defaultdict(dict)
    for item in coefficient_rows:
        grouped[item["relation_id"]][item["coefficient"]] = float(item["value"])
    bibliography = bibtex_entries()

    lines = [
        "# This file is generated by scripts/generate_julia_registry.py.",
        "# Edit the canonical CSV data or explicit evaluator implementations instead.",
        "",
    ]
    for row in relations:
        source = sources[row["source_id"]]
        coeffs = grouped[row["relation_id"]] or fixed_coefficients(row["equation_latex"])
        family = row["family"]
        coefficient_literal = "(; " + ", ".join(f"{key} = {value!r}" for key, value in coeffs.items()) + ")"
        input_values = inputs(row)
        input_literal = "(" + ", ".join(f":{value}" for value in input_values) + ("," if len(input_values) == 1 else "") + ")"
        bounds, assumptions = domain(row)
        assumptions_literal = "[" + ", ".join(julia_string(value) for value in assumptions) + "]"
        pub = publication_id(source)
        doi = "nothing" if not source["doi"] else julia_string(source["doi"])
        authors = "[" + ", ".join(julia_string(value.strip()) for value in source["authors"].split(";")) + "]"
        bib = bibliography.get(source["arxiv_id"])
        if bib is None:
            raise ValueError(f"missing BibTeX for {source['arxiv_id']}")
        output_unit = "km" if quantity(row).startswith("R_") else "dimensionless" if family == "tidal_coupling_rational_fit" else "kHz"
        lines.extend([
            "let",
            f"    coefficients = {coefficient_literal}",
            "    _register!(RelationSpec(",
            f"        RelationID({julia_string(row['relation_id'])}), :{pub}, :{quantity(row)}, {input_literal},",
            f"        {symbol(family)}, {symbol(row['relation_id'])},",
            f"        {julia_string(row['equation_latex'])}, {julia_string(canonical_expression(row))}, coefficients, :{output_unit},",
            f"        DomainSpec({julia_string(row['applicability'])}, {bounds}, {assumptions_literal}),",
            "        SourceInfo(",
            f"            :{pub}, {julia_string(row['source_id'])}, {julia_string(source['title'])}, {authors},",
            f"            {int(source['publication_year'])}, {doi}, {julia_string(source['arxiv_id'])}, {julia_string(source['abstract_url'])},",
            f"            {julia_string(row['equation_label'])}, {julia_string(row['source_table'])}, {julia_string(row['source_path'])}, {julia_string(bib)},",
            "        ),",
            f"        {symbol(row['review_status'])}, :implemented, _evaluator({symbol(family)}, coefficients),",
            "    ))",
            "end",
            "",
        ])
    return "\n".join(lines), len(relations)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the Julia relation registry from reviewed CSV data."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the committed registry differs from generated content",
    )
    args = parser.parse_args()

    content, relation_count = generated_content()
    destination = ROOT / "src" / "GeneratedRegistry.jl"
    if args.check:
        if not destination.exists() or destination.read_text() != content:
            parser.error(
                "src/GeneratedRegistry.jl is stale; run "
                "python3 scripts/generate_julia_registry.py"
            )
        print(f"Verified {destination.relative_to(ROOT)} ({relation_count} relations).")
        return

    destination.write_text(content)
    print(f"Generated {destination.relative_to(ROOT)} with {relation_count} relations.")


if __name__ == "__main__":
    main()
