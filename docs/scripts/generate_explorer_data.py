#!/usr/bin/env python3
"""Validate canonical CSVs and generate the static explorer representation."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import subprocess
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
OUT = ROOT / "docs" / "src" / "assets" / "data"
DOWNLOADS = ROOT / "docs" / "src" / "assets" / "downloads"
BIBLIOGRAPHY = ROOT / "papers" / "bibliography.bib"

FILES = {
    "waveforms": DATA / "waveforms.csv",
    "eos": DATA / "eos.csv",
    "sources": DATA / "sources.csv",
    "provenance": DATA / "provenance.csv",
    "relations": DATA / "relations" / "relations.csv",
    "coefficients": DATA / "relations" / "coefficients.csv",
}

REQUIRED = {
    "waveforms": {"id", "source_id", "eos", "mtot_msun", "q", "f_peak_khz", "f_2_0_khz", "f_spiral_khz"},
    "eos": {"id", "source_id", "eos"},
    "sources": {"source_id", "arxiv_id", "title", "authors", "abstract_url"},
    "provenance": {"record_type", "record_id", "source_id", "source_path", "review_status"},
    "relations": {"relation_id", "source_id", "family", "equation_latex", "dependent_variable", "dependent_unit", "independent_variables"},
    "coefficients": {"relation_id", "coefficient", "term", "value"},
}

NUMERIC = {
    "waveforms": {"m1_msun", "m2_msun", "mtot_msun", "mchirp_msun", "q", "q_original", "lambda1", "lambda2", "lambda_tilde", "f_peak_khz", "f_2_0_khz", "f_spiral_khz", "f_radial_khz", "f_peak_early_khz", "f_peak_late_khz", "f_peak_mean_khz", "f_peak_instantaneous_khz", "f_merger_khz", "f_gw_initial_hz"},
    "eos": {"r_1_2_km", "r_1_4_km", "r_1_6_km", "r_1_8_km", "m_tov_msun"},
    "relations": {"r_squared_adjusted", "max_residual", "mean_residual", "residual_std"},
    "coefficients": {"value"},
    "provenance": {"source_line_start", "source_line_end"},
}


def read_table(name: str) -> tuple[list[str], list[dict]]:
    path = FILES[name]
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        missing = REQUIRED[name] - set(fields)
        if missing:
            raise ValueError(f"{path}: missing required columns {sorted(missing)}")
        rows = list(reader)
    for line, row in enumerate(rows, 2):
        if None in row:
            raise ValueError(f"{path}:{line}: row has more values than headers")
    return fields, rows


def scalar(name: str, key: str, value: str):
    if value == "":
        return None
    if key not in NUMERIC.get(name, set()):
        return value
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{FILES[name]}: invalid numeric value {value!r} in {key}") from exc
    if not number.is_finite():
        raise ValueError(f"{FILES[name]}: non-finite value {value!r} in {key}")
    return int(number) if number == number.to_integral() else float(number)


def convert(name: str, row: dict) -> dict:
    return {key: scalar(name, key, value) for key, value in row.items()}


def unique(rows: list[dict], key: str, label: str) -> None:
    duplicates = [value for value, count in Counter(r[key] for r in rows).items() if count > 1]
    if duplicates:
        raise ValueError(f"duplicate {label}: {duplicates[:5]}")


def last_updated() -> str:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", "data"], cwd=ROOT,
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        return result or "uncommitted dataset"
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def bibliography_by_arxiv() -> dict[str, str]:
    """Return complete generated BibTeX entries indexed by bare arXiv ID."""
    content = BIBLIOGRAPHY.read_text(encoding="utf-8")
    entries = re.findall(r"(?ms)^@\w+\{.*?^\}\s*$", content)
    result = {}
    for entry in entries:
        match = re.search(r"(?m)^\s*eprint\s*=\s*\{([^}]+)\}", entry)
        if match:
            result[match.group(1).strip()] = entry.strip()
    return result


def coefficient_map(coefficients: list[dict]) -> dict[str, int | float]:
    return {item["coefficient"]: item["value"] for item in coefficients}


def fixed_mass_coefficients(equation: str) -> tuple[float, float, float]:
    """Extract c0, c1, c2 from the reviewed fixed-mass quadratic expression."""
    rhs = equation.strip().strip("$").split("=", 1)[1]
    number = r"[+-]?\s*\d+(?:\.\d+)?(?:\s*\\times\s*10\^\{[+-]?\d+\})?"
    constant = re.match(rf"\s*({number})", rhs)
    variable_terms = re.findall(rf"({number})\s*(?=(?:\\left\s*\()?\s*(?:R_|\\Lambda))", rhs)
    if constant is None or len(variable_terms) != 2:
        raise ValueError(f"unable to parse fixed-mass relation: {equation}")

    def numeric(token: str) -> float:
        normalized = re.sub(r"\s+", "", token)
        normalized = re.sub(r"\\times10\^\{([+-]?\d+)\}", r"e\1", normalized)
        return float(normalized)

    return numeric(constant.group(1)), numeric(variable_terms[0]), numeric(variable_terms[1])


def code_examples(row: dict, coefficients: list[dict]) -> dict[str, str]:
    """Build transparent, dependency-free Julia and Python implementations."""
    family = row["family"]
    values = coefficient_map(coefficients)
    py_name = "empirical_relation"
    jl_name = "empirical_relation"

    def pair(arguments: str, expression: str, comment: str) -> dict[str, str]:
        python_expression = expression.replace("^", "**")
        return {
            "python": f"def {py_name}({arguments}):\n    \"\"\"{comment}\"\"\"\n    return {python_expression}\n",
            "julia": f'"""{comment}"""\nfunction {jl_name}({arguments})\n    return {expression}\nend\n',
        }

    if family == "frequency_from_radius":
        v = values
        expression = f"{v['b0']} + {v['b1']}*mchirp_msun + {v['b2']}*radius_km + {v['b3']}*mchirp_msun^2 + {v['b4']}*radius_km*mchirp_msun + {v['b5']}*radius_km^2"
        return pair("mchirp_msun, radius_km", f"mchirp_msun * ({expression})", "Return the fitted frequency in kHz.")
    if family == "radius_from_frequency":
        v = values
        ratio = "frequency_khz / mchirp_msun"
        expression = f"{v['b0']} + {v['b1']}*mchirp_msun + {v['b2']}*({ratio}) + {v['b3']}*mchirp_msun^2 + {v['b4']}*frequency_khz + {v['b5']}*({ratio})^2"
        return pair("mchirp_msun, frequency_khz", expression, "Return the fitted radius in km.")
    if family in {"frequency_from_tidal_deformability", "secondary_frequency_from_tidal_deformability", "spiral_frequency_from_tidal_deformability"}:
        v = values
        expression = f"({v['b0']} + {v['b1']}*mchirp_msun + {v['b2']}*lambda_tilde^(-0.5)) / mchirp_msun"
        return pair("mchirp_msun, lambda_tilde", expression, "Return the fitted frequency in kHz.")
    if family == "tidal_coupling_rational_fit":
        v = values
        expression = f"{v['Q0']} * (1 + {v['n1']}*kappa2T + {v['n2']}*kappa2T^2) / (1 + {v['d1']}*kappa2T)"
        return pair("kappa2T", expression, "Return the dimensionless fitted quantity.")
    if family in {"merger_frequency_from_tidal_deformability", "postmerger_frequency_from_tidal_deformability"}:
        prefix = "a" if family.startswith("merger_") else "c"
        v = values
        exponent = f"({v[prefix + '00']} + {v[prefix + '01']}*eta) + ({v[prefix + '10']} + {v[prefix + '11']}*eta)*lambda_tilde^(1/5)"
        return pair("total_mass_msun, eta, lambda_tilde", f"10^({exponent}) / total_mass_msun", "Return the fitted frequency in Hz.")
    if family == "F1_tidal_mass_ratio_frequency_fit":
        v = values
        exponent = f"{v['a0']} + ({v['b0']} + {v['b1']}*q + {v['b2']}*q^2)*kappa2T^{v['n']}"
        return pair("total_mass_msun, q, kappa2T", f"10^({exponent}) / total_mass_msun", "Return the fitted frequency in Hz.")
    if family == "fixed_mass_peak_frequency":
        c0, c1, c2 = fixed_mass_coefficients(row["equation_latex"])
        argument = "lambda_one_fifth" if "Lambda" in row["independent_variables"] else "radius_km"
        return pair(argument, f"{c0} + {c1}*{argument} + {c2}*{argument}^2", "Return the fitted peak frequency in kHz.")
    raise ValueError(f"no implementation template for relation family {family!r}")


def main() -> None:
    loaded = {name: read_table(name) for name in FILES}
    rows = {name: value[1] for name, value in loaded.items()}
    unique(rows["waveforms"], "id", "waveform IDs")
    unique(rows["eos"], "id", "EOS IDs")
    unique(rows["sources"], "source_id", "source IDs")
    unique(rows["relations"], "relation_id", "relation IDs")

    bibtex = bibliography_by_arxiv()
    sources = {row["source_id"]: convert("sources", row) for row in rows["sources"]}
    for source in sources.values():
        source["bibtex"] = bibtex.get(source["arxiv_id"])
    provenance = {}
    for row in rows["provenance"]:
        # Raw LaTeX is intentionally excluded from the compact browser payload.
        item = convert("provenance", {k: v for k, v in row.items() if k != "raw_latex"})
        provenance.setdefault(row["record_id"], []).append(item)

    waveform_records = []
    for row in rows["waveforms"]:
        if row["source_id"] not in sources:
            raise ValueError(f"waveform {row['id']} has unknown source {row['source_id']}")
        if row["id"] not in provenance:
            raise ValueError(f"waveform {row['id']} has no provenance")
        item = convert("waveforms", row)
        item["source"] = sources[row["source_id"]]
        item["provenance"] = provenance[row["id"]]
        waveform_records.append(item)

    coefficient_groups: dict[str, list[dict]] = {}
    relation_ids = {row["relation_id"] for row in rows["relations"]}
    for row in rows["coefficients"]:
        if row["relation_id"] not in relation_ids:
            raise ValueError(f"coefficient has unknown relation {row['relation_id']}")
        coefficient_groups.setdefault(row["relation_id"], []).append(convert("coefficients", row))

    relation_records = []
    for row in rows["relations"]:
        if row["source_id"] not in sources:
            raise ValueError(f"relation {row['relation_id']} has unknown source")
        item = convert("relations", row)
        item["source"] = sources[row["source_id"]]
        item["coefficients"] = coefficient_groups.get(row["relation_id"], [])
        item["code"] = code_examples(row, item["coefficients"])
        item["provenance"] = provenance.get(row["relation_id"], [])
        item["implementation_status"] = "catalogued"
        relation_records.append(item)

    eos_records = []
    for row in rows["eos"]:
        if row["source_id"] not in sources:
            raise ValueError(f"EOS {row['id']} has unknown source")
        item = convert("eos", row)
        item["source"] = sources[row["source_id"]]
        eos_records.append(item)

    digest = hashlib.sha256()
    for path in FILES.values():
        digest.update(path.read_bytes())
    metadata = {
        "schema_version": 1,
        "last_updated": last_updated(),
        "dataset_sha256": digest.hexdigest(),
        "counts": {"waveforms": len(waveform_records), "eos": len(eos_records), "sources": len(sources), "relations": len(relation_records), "coefficients": len(rows["coefficients"])},
        "canonical_files": {name: str(path.relative_to(ROOT)) for name, path in FILES.items()},
    }

    OUT.mkdir(parents=True, exist_ok=True)
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    payloads = {"waveforms": waveform_records, "relations": relation_records, "eos": eos_records, "metadata": metadata}
    for name, payload in payloads.items():
        (OUT / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    for name in ("waveforms", "eos", "sources", "provenance"):
        shutil.copyfile(FILES[name], DOWNLOADS / FILES[name].name)
    shutil.copyfile(FILES["relations"], DOWNLOADS / "relations.csv")
    shutil.copyfile(FILES["coefficients"], DOWNLOADS / "coefficients.csv")
    print(f"Generated {len(waveform_records)} waveforms and {len(relation_records)} relations ({metadata['dataset_sha256'][:12]}).")


if __name__ == "__main__":
    main()
