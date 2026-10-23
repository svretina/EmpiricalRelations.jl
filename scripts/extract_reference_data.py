#!/usr/bin/env python3
"""Extract the Vretinaris et al. (2020) reference tables into public CSVs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


SOURCE_ID = "arxiv-1910-10856"
ARXIV_ID = "1910.10856"
EXPECTED_SOURCE_COUNT = 31
DEFAULT_SOURCE = Path("papers/1910.10856_vretinaris_2020/source")

WAVEFORM_FIELDS = [
    "id", "source_id", "catalogue", "simulation_id", "eos", "eos_variant",
    "m1_msun", "m2_msun", "mtot_msun", "mchirp_msun", "q", "q_definition",
    "q_original", "q_original_definition", "lambda1", "lambda2", "lambda_tilde",
    "f_peak_khz", "f_2_0_khz", "f_2_0_status", "f_spiral_khz", "f_spiral_status",
    "f_radial_khz", "f_peak_early_khz", "f_peak_late_khz", "f_peak_mean_khz",
    "f_peak_instantaneous_khz", "f_merger_khz",
    "f_gw_initial_hz", "spectral_type", "simulation_code", "numerical_method",
    "waveform_extraction", "source_table", "notes",
]
FREQUENCY_FIELDS = [
    "f_peak_khz", "f_2_0_khz", "f_spiral_khz", "f_radial_khz",
    "f_peak_early_khz", "f_peak_late_khz", "f_peak_mean_khz",
    "f_peak_instantaneous_khz", "f_merger_khz", "f_gw_initial_hz",
]
EOS_FIELDS = [
    "id", "source_id", "eos", "eos_variant", "r_1_2_km", "r_1_4_km",
    "r_1_6_km", "r_1_8_km", "m_tov_msun", "definition_notes", "source_table",
]
RELATION_FIELDS = [
    "relation_id", "source_id", "family", "equation_label", "equation_latex",
    "dependent_variable", "dependent_unit", "independent_variables",
    "calibration_population", "applicability", "source_table", "source_path",
    "r_squared_adjusted", "max_residual", "mean_residual", "residual_std",
    "residual_unit", "review_status", "notes",
]
COEFFICIENT_FIELDS = ["relation_id", "coefficient", "term", "value", "source_id", "source_path"]
PROVENANCE_FIELDS = [
    "record_type", "record_id", "source_id", "source_path", "source_line_start",
    "source_line_end", "table_label", "raw_latex", "extraction_method", "review_status",
]
SOURCE_FIELDS = [
    "source_id", "arxiv_id", "resolved_version", "title", "authors", "publication_year",
    "publication_date", "doi", "abstract_url", "local_paper_dir", "local_source_root",
    "main_tex", "pdf_sha256", "source_sha256", "source_status", "tex_status", "license_note",
]
TABLE_INVENTORY_FIELDS = [
    "table_id", "source_id", "arxiv_id", "source_path", "line_start", "line_end", "label",
    "caption", "column_count", "row_count", "numeric_row_count", "candidate_kind", "review_status",
]
DEPENDENCY_FIELDS = [
    "source_id", "arxiv_id", "source_path", "line", "command", "target_raw", "target_resolved", "exists",
]
COVERAGE_FIELDS = [
    "source_id", "arxiv_id", "title", "structural_status", "tables", "table_rows",
    "equations", "empirical_equation_candidates", "dependencies", "reviewed_adapter",
    "public_waveforms", "public_eos", "public_relations", "scientific_review_status", "notes",
]
PUBLISHED_TABLE_FIELDS = TABLE_INVENTORY_FIELDS
PUBLISHED_CELL_FIELDS = [
    "cell_id", "table_id", "source_id", "source_path", "table_label", "row_index",
    "column_index", "line_start", "line_end", "value_latex", "value_text", "numeric_value",
    "candidate_kind", "review_status",
]
PUBLISHED_EQUATION_FIELDS = [
    "equation_id", "source_id", "source_path", "line_start", "line_end", "label",
    "equation_latex", "context_latex", "empirical_relation_candidate", "review_status",
]
MEASUREMENT_EXTRA_FIELDS = [
    "measurement_id", "waveform_id", "source_id", "simulation_id", "quantity", "value",
    "unit", "uncertainty_plus", "uncertainty_minus", "value_text", "status", "source_path",
    "table_label", "line_start", "notes",
]


@dataclass(frozen=True)
class LatexRow:
    cells: list[str]
    raw: str
    line_start: int
    line_end: int


def strip_comments(text: str) -> str:
    return re.sub(r"(?<!\\)%.*", "", text)


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def table_label(text: str) -> str:
    match = re.search(r"\\label\{([^}]+)\}", text)
    return match.group(1) if match else ""


def caption(text: str) -> str:
    match = re.search(r"\\caption\{(.*?)\}\s*\\begin\{tabular", text, re.S)
    return clean_latex(match.group(1)) if match else ""


def tabular_bodies(text: str) -> list[tuple[str, int]]:
    """Return every tabular/tabular* body, including tables with width arguments."""
    pattern = re.compile(
        r"\\begin\{tabular\*?\}(?P<args>[^\n]*?)\n(?P<body>.*?)"
        r"\\end\{tabular\*?\}", re.S,
    )
    return [(match.group("body"), match.start("body")) for match in pattern.finditer(text)]


def split_latex_rows(text: str) -> list[LatexRow]:
    """Split a tabular body on unescaped LaTeX row terminators."""
    rows: list[LatexRow] = []
    bodies = tabular_bodies(text)
    if not bodies:
        raise ValueError("no tabular environment found")
    for body, body_offset in bodies:
        start = 0
        index = 0
        while index < len(body) - 1:
            if body[index:index + 2] == "\\\\" and (index == 0 or body[index - 1] != "\\"):
                raw = body[start:index].strip()
                absolute_start = body_offset + start
                absolute_end = body_offset + index + 2
                cells = split_cells(raw)
                if raw and cells:
                    rows.append(LatexRow(cells, raw, line_number(text, absolute_start), line_number(text, absolute_end)))
                start = index + 2
                index += 2
            else:
                index += 1
    return rows


def split_cells(row: str) -> list[str]:
    row = re.sub(r"^\s*(?:\\hline|\\hhline\{[^}]*\})\s*", "", row)
    cells: list[str] = []
    depth = 0
    start = 0
    for index, character in enumerate(row):
        if character == "{" and (index == 0 or row[index - 1] != "\\"):
            depth += 1
        elif character == "}" and (index == 0 or row[index - 1] != "\\"):
            depth = max(0, depth - 1)
        elif character == "&" and depth == 0 and (index == 0 or row[index - 1] != "\\"):
            cells.append(row[start:index].strip())
            start = index + 1
    cells.append(row[start:].strip())
    return cells


def unwrap_command(text: str, command: str) -> str:
    pattern = re.compile(rf"\\{command}(?:\[[^]]*\])?\{{([^{{}}]*)\}}")
    previous = None
    while previous != text:
        previous = text
        text = pattern.sub(r"\1", text)
    return text


def clean_latex(value: str) -> str:
    value = re.sub(r"\\(?:hline|hhline\{[^}]*\})", "", value)
    for command in ("textbf", "mathrm", "rm", "textit", "it", "mathbf"):
        value = unwrap_command(value, command)
    value = value.replace("$", "").replace("{", "").replace("}", "")
    value = value.replace("\\,", " ").replace("~", " ")
    return re.sub(r"\s+", " ", value).strip()


def number(value: str) -> float | None:
    cleaned = clean_latex(value).strip()
    if cleaned in {"", "-", "--", "\\ldots", "…"}:
        return None
    cleaned = cleaned.replace("−", "-")
    if not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", cleaned):
        raise ValueError(f"not a numeric table cell: {value!r} -> {cleaned!r}")
    return float(cleaned)


def central_number(value: str) -> float | None:
    """Extract a central numeric value while retaining the original cell separately."""
    cleaned = clean_latex(value).replace("−", "-")
    if cleaned.strip() in {"", "-", "--", "---", "x", "\\ldots", "…"}:
        return None
    match = re.search(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", cleaned)
    return float(match.group(0)) if match else None


def format_value(value: Any) -> Any:
    if value is None:
        return ""
    return value


def stable_id(*parts: str) -> str:
    return "-".join(re.sub(r"[^a-z0-9]+", "-", part.lower()).strip("-") for part in parts)


def chirp_mass(m1: float, m2: float) -> float:
    return (m1 * m2) ** (3 / 5) / (m1 + m2) ** (1 / 5)


def table_rows(path: Path) -> tuple[str, list[LatexRow]]:
    text = strip_comments(path.read_text(encoding="utf-8"))
    return text, split_latex_rows(text)


def row_provenance(record_type: str, record_id: str, relative_path: str, label: str,
                   row: LatexRow, review_status: str = "verified") -> dict[str, Any]:
    return {
        "record_type": record_type, "record_id": record_id, "source_id": SOURCE_ID,
        "source_path": relative_path, "source_line_start": row.line_start,
        "source_line_end": row.line_end, "table_label": label, "raw_latex": row.raw,
        "extraction_method": "deterministic_latex_table_parser", "review_status": review_status,
    }


def make_waveform(catalogue: str, index: int, cells: list[str], relative_path: str) -> dict[str, Any]:
    if catalogue == "CFC/SPH":
        eos, fpeak, f20, fspiral, m1, m2, mchirp, q_original = cells
        fgw = None
        simulation_code = "3D SPH"
        numerical_method = "general-relativistic conformal-flatness approximation (CFC/SPH)"
        waveform_extraction = "modified quadrupole formula; Tukey window alpha=0.1; zero padded to 16384 samples"
        secondary_status = "measured" if number(f20) is not None else "not_reported_or_not_identified"
        spiral_status = "measured" if number(fspiral) is not None else "not_reported_or_not_identified"
        q_definition_original = "m1/m2 <= 1"
    else:
        eos, fpeak, fgw, m1, m2, mchirp, q_original = cells
        f20 = fspiral = "-"
        simulation_code = "CoRe contributing full-GR codes"
        numerical_method = "full general relativity; high-resolution shock-capturing; selected highest resolution R01"
        waveform_extraction = "same spectral extraction procedure as CFC/SPH; only f_peak reported"
        secondary_status = spiral_status = "not_reported_for_catalogue"
        q_definition_original = "min(m1,m2)/max(m1,m2) <= 1 (as tabulated)"
    m1_value, m2_value = number(m1), number(m2)
    q_value = min(m1_value, m2_value) / max(m1_value, m2_value)
    record_id = f"{SOURCE_ID}-{stable_id(catalogue)}-{index:04d}"
    return {
        "id": record_id, "source_id": SOURCE_ID, "catalogue": catalogue,
        "simulation_id": "", "eos": clean_latex(eos).upper(), "eos_variant": "",
        "m1_msun": m1_value, "m2_msun": m2_value, "mtot_msun": m1_value + m2_value,
        "mchirp_msun": number(mchirp), "q": q_value, "q_definition": "min(m1,m2)/max(m1,m2) <= 1",
        "q_original": number(q_original), "q_original_definition": q_definition_original,
        "lambda1": "", "lambda2": "", "lambda_tilde": "",
        "f_peak_khz": number(fpeak), "f_2_0_khz": number(f20), "f_2_0_status": secondary_status,
        "f_spiral_khz": number(fspiral), "f_spiral_status": spiral_status,
        "f_gw_initial_hz": number(fgw) if fgw is not None else None,
        "spectral_type": "unknown", "simulation_code": simulation_code,
        "numerical_method": numerical_method, "waveform_extraction": waveform_extraction,
        "source_table": relative_path,
        "notes": "Original simulation identifier is not included in the published table.",
    }


def extract_waveforms(source: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    report: dict[str, Any] = {}
    specifications = [
        ("CFC/SPH", "tables/bauswein_data.tex", 16),
        ("CoRe", "tables/CORE_data.tex", 7),
    ]
    for catalogue, relative, width in specifications:
        text, rows = table_rows(source / relative)
        label = table_label(text)
        def is_data_row(row: LatexRow) -> bool:
            if len(row.cells) != width:
                return False
            try:
                return number(row.cells[1]) is not None and (width != 16 or number(row.cells[9]) is not None)
            except ValueError:
                return False

        data_rows = [row for row in rows if is_data_row(row)]
        count_before = len(records)
        for row in data_rows:
            chunks = [row.cells[offset:offset + 8] for offset in range(0, width, 8)] if width == 16 else [row.cells]
            for chunk in chunks:
                index = len(records) - count_before + 1
                record = make_waveform(catalogue, index, chunk, relative)
                records.append(record)
                provenance.append(row_provenance("waveform", record["id"], relative, label, row))
        report[catalogue] = {
            "source_path": relative, "table_label": label, "caption": caption(text),
            "latex_rows": len(data_rows), "waveform_records": len(records) - count_before,
        }
    return records, provenance, report


def extract_eos(source: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    relative = "tables/TOV_info.tex"
    text, rows = table_rows(source / relative)
    label = table_label(text)
    def is_eos_row(row: LatexRow) -> bool:
        if len(row.cells) != 5:
            return False
        try:
            return all(number(cell) is not None for cell in row.cells[1:])
        except ValueError:
            return False

    data_rows = [row for row in rows if is_eos_row(row)]
    records = []
    provenance = []
    for row in data_rows:
        eos = clean_latex(row.cells[0])
        record_id = f"{SOURCE_ID}-eos-{eos.lower()}"
        record = {
            "id": record_id, "source_id": SOURCE_ID, "eos": eos, "eos_variant": "",
            "r_1_2_km": number(row.cells[1]), "r_1_4_km": number(row.cells[2]),
            "r_1_6_km": number(row.cells[3]), "r_1_8_km": number(row.cells[4]),
            "m_tov_msun": "", "definition_notes": "Cold, nonrotating stellar models for the source-specific EOS definition.",
            "source_table": relative,
        }
        records.append(record)
        provenance.append(row_provenance("eos", record_id, relative, label, row))
    return records, provenance, {"source_path": relative, "table_label": label, "caption": caption(text), "eos_records": len(records)}


def multicolumn_heading(raw: str) -> str | None:
    match = re.search(r"\\multicolumn\{\d+\}\{[^}]*\}\{(.*?)\}\s*$", raw, re.S)
    return clean_latex(match.group(1)) if match else None


def relation_group(heading: str, family: str) -> tuple[str, str, str]:
    population = "equal_masses" if "equal masses" in heading else "all_masses"
    if family == "frequency_from_radius":
        dependent = "f_peak_khz" if "peak" in heading else ("f_2_0_khz" if "2-0" in heading else "f_spiral_khz")
        applicability = "equal masses only" if population == "equal_masses" else "equal and unequal masses"
    else:
        radius_match = re.search(r"R_?\s*([0-9.]+)", heading)
        dependent = f"r_{radius_match.group(1).replace('.', '_')}_km" if radius_match else "radius_km"
        if "<" in heading:
            range_text = "M_chirp < 1.3 Msun"
        elif ">" in heading:
            range_text = "M_chirp > 1.3 Msun"
        else:
            range_text = "full M_chirp range"
        applicability = range_text + ("; equal masses only" if population == "equal_masses" else "; equal and unequal masses")
    return dependent, population, applicability


def clean_radius_name(value: str) -> str:
    cleaned = clean_latex(value)
    match = re.search(r"R_?([0-9.]+)", cleaned)
    if not match:
        raise ValueError(f"cannot identify radius from {value!r}")
    return match.group(1)


def clean_frequency_name(value: str) -> str:
    cleaned = clean_latex(value).lower()
    if "peak" in cleaned:
        return "f_peak_khz"
    if "2-0" in cleaned:
        return "f_2_0_khz"
    if "spiral" in cleaned:
        return "f_spiral_khz"
    raise ValueError(f"cannot identify frequency from {value!r}")


def extract_relation_table(source: Path, relative: str, family: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    text, rows = table_rows(source / relative)
    label = table_label(text)
    heading = ""
    relations: list[dict[str, Any]] = []
    coefficients: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    terms_by_family = {
        "frequency_from_radius": ["1", "M_chirp", "R_x", "M_chirp^2", "R_x*M_chirp", "R_x^2"],
        "radius_from_frequency": ["1", "M_chirp", "f_j/M_chirp", "M_chirp^2", "f_j", "(f_j/M_chirp)^2"],
    }
    equation_by_family = {
        "frequency_from_radius": "f_j/M_chirp = b0 + b1*M_chirp + b2*R_x + b3*M_chirp^2 + b4*R_x*M_chirp + b5*R_x^2",
        "radius_from_frequency": "R_x = b0 + b1*M_chirp + b2*f_j/M_chirp + b3*M_chirp^2 + b4*f_j + b5*(f_j/M_chirp)^2",
    }
    for row in rows:
        group = multicolumn_heading(row.raw)
        if group:
            heading = group
            continue
        if len(row.cells) != 11 or not heading:
            continue
        try:
            numeric = [number(cell) for cell in row.cells[1:]]
        except ValueError:
            continue
        if any(value is None for value in numeric):
            continue
        dependent, population, applicability = relation_group(heading, family)
        if family == "frequency_from_radius":
            radius_mass = clean_radius_name(row.cells[0])
            frequency = dependent
            independent = f"mchirp_msun;r_{radius_mass.replace('.', '_')}_km"
            qualifier = f"{frequency}-r{radius_mass}-{population}"
            residual_unit = "kHz"
        else:
            radius_mass = re.search(r"r_([0-9]+_[0-9]+)_km", dependent).group(1).replace("_", ".")
            frequency = clean_frequency_name(row.cells[0])
            independent = f"mchirp_msun;{frequency}"
            qualifier = f"r{radius_mass}-{frequency}-{population}"
            residual_unit = "km"
        relation_id = f"{SOURCE_ID}-{stable_id(family, qualifier)}"
        values = numeric[:6]
        relation = {
            "relation_id": relation_id, "source_id": SOURCE_ID, "family": family,
            "equation_label": "fRM" if family == "frequency_from_radius" else "RfM",
            "equation_latex": equation_by_family[family], "dependent_variable": dependent,
            "dependent_unit": "kHz" if family == "frequency_from_radius" else "km",
            "independent_variables": independent, "calibration_population": population,
            "applicability": applicability, "source_table": label, "source_path": relative,
            "r_squared_adjusted": numeric[6], "max_residual": numeric[7],
            "mean_residual": numeric[8], "residual_std": numeric[9], "residual_unit": residual_unit,
            "review_status": "verified_from_coefficient_table",
            "notes": "Residual statistics and coefficients are transcribed deterministically from the published table.",
        }
        relations.append(relation)
        for coefficient, term, value in zip((f"b{i}" for i in range(6)), terms_by_family[family], values):
            coefficients.append({
                "relation_id": relation_id, "coefficient": coefficient, "term": term,
                "value": value, "source_id": SOURCE_ID, "source_path": relative,
            })
        provenance.append(row_provenance("relation", relation_id, relative, label, row))
    return relations, coefficients, provenance


def extract_equations(source: Path) -> list[dict[str, Any]]:
    relative = "article.tex"
    text = strip_comments((source / relative).read_text(encoding="utf-8"))
    equations = []
    for match in re.finditer(r"\\begin\{equation\}(.*?)\\end\{equation\}", text, re.S):
        body = match.group(1).strip()
        label_match = re.search(r"\\label\{([^}]+)\}", body)
        label = label_match.group(1) if label_match else ""
        equation = re.sub(r"\\label\{[^}]+\}", "", body).strip()
        context_start = max(0, text.rfind("\n\n", 0, match.start()))
        context_end = text.find("\n\n", match.end())
        if context_end < 0:
            context_end = min(len(text), match.end() + 1000)
        equations.append({
            "source_id": SOURCE_ID, "source_path": relative,
            "line_start": line_number(text, match.start()), "line_end": line_number(text, match.end()),
            "label": label, "equation_latex": equation,
            "context_latex": text[context_start:context_end].strip(),
        })
    return equations


def explicit_relation(equations: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    equation = next(item for item in equations if item["label"] == "fpeak2DL")
    relation_id = f"{SOURCE_ID}-fpeak-lambda-tilde-mchirp-all-masses"
    relation = {
        "relation_id": relation_id, "source_id": SOURCE_ID, "family": "frequency_from_tidal_deformability",
        "equation_label": "fpeak2DL", "equation_latex": equation["equation_latex"],
        "dependent_variable": "f_peak_khz*mchirp_msun", "dependent_unit": "kHz Msun",
        "independent_variables": "mchirp_msun;lambda_tilde^(-1/2)", "calibration_population": "all_masses",
        "applicability": "CFC/SPH catalogue; equal and unequal masses",
        "source_table": "", "source_path": "article.tex", "r_squared_adjusted": 0.985,
        "max_residual": 0.302, "mean_residual": "", "residual_std": "", "residual_unit": "kHz",
        "review_status": "verified_from_equation_and_context",
        "notes": "Maximum frequency residual and R^2 are stated in the paragraph following Eq. fpeak2DL.",
    }
    coefficients = [
        {"relation_id": relation_id, "coefficient": "b0", "term": "1", "value": 1.392, "source_id": SOURCE_ID, "source_path": "article.tex"},
        {"relation_id": relation_id, "coefficient": "b1", "term": "M_chirp", "value": -0.108, "source_id": SOURCE_ID, "source_path": "article.tex"},
        {"relation_id": relation_id, "coefficient": "b2", "term": "lambda_tilde^(-1/2)", "value": 51.70, "source_id": SOURCE_ID, "source_path": "article.tex"},
    ]
    provenance = {
        "record_type": "relation", "record_id": relation_id, "source_id": SOURCE_ID,
        "source_path": "article.tex", "source_line_start": equation["line_start"],
        "source_line_end": equation["line_end"], "table_label": "fpeak2DL",
        "raw_latex": equation["equation_latex"], "extraction_method": "reviewed_equation_adapter",
        "review_status": "verified",
    }
    return relation, coefficients, provenance


def source_id_for(arxiv_id: str) -> str:
    return "arxiv-" + re.sub(r"[^a-zA-Z0-9]+", "-", arxiv_id).strip("-").lower()


def load_source_registry(papers_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for metadata_path in sorted(papers_dir.glob("*/metadata.json")):
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        arxiv_id = metadata["arxiv_id"]
        paper_dir = metadata_path.parent
        source_root = paper_dir / "source"
        authors = metadata.get("authors") or []
        records.append({
            "source_id": source_id_for(arxiv_id), "arxiv_id": arxiv_id,
            "resolved_version": metadata.get("resolved_version"), "title": metadata.get("title"),
            "authors": "; ".join(authors), "publication_year": metadata.get("publication_year"),
            "publication_date": metadata.get("publication_date"), "doi": metadata.get("doi"),
            "abstract_url": metadata.get("abstract_url"), "local_paper_dir": paper_dir.as_posix(),
            "local_source_root": source_root.as_posix() if source_root.is_dir() else "",
            "main_tex": metadata.get("main_tex"),
            "pdf_sha256": metadata.get("checksums", {}).get("pdf_sha256"),
            "source_sha256": metadata.get("checksums", {}).get("source_sha256"),
            "source_status": metadata.get("source_status"), "tex_status": metadata.get("tex_status"),
            "license_note": "Consult the original publication and arXiv record for reuse terms.",
        })
    return records


def numeric_cell_count(cells: list[str]) -> int:
    count = 0
    for cell in cells:
        try:
            count += number(cell) is not None
        except ValueError:
            pass
    return count


def classify_table(path: str, table_caption: str, rows: list[LatexRow]) -> str:
    text = (path + " " + table_caption + " " + " ".join(row.raw for row in rows[:3])).lower()
    if any(term in text for term in ("f_peak", "f_{\\rm peak}", "f_{\\mathrm{peak}}", "postmerger", "waveform")) and any(term in text for term in ("m_1", "m1", "mass", "eos")):
        return "waveform_measurement_candidate"
    if "radius" in text and "eos" in text:
        return "eos_property_candidate"
    if any(term in text for term in ("coefficient", "regression", "residual", "b_0", "b0")):
        return "empirical_relation_candidate"
    if sum(numeric_cell_count(row.cells) for row in rows) >= 3:
        return "numeric_table_candidate"
    return "descriptive_table"


def resolve_dependency(source_root: Path, tex_path: Path, target: str) -> tuple[str, bool]:
    cleaned = target.strip()
    candidate = tex_path.parent / cleaned
    possibilities = [candidate]
    if not candidate.suffix:
        possibilities.append(candidate.with_suffix(".tex"))
    for path in possibilities:
        try:
            relative = path.resolve().relative_to(source_root.resolve())
        except ValueError:
            continue
        if path.is_file():
            return relative.as_posix(), True
    try:
        return possibilities[-1].resolve().relative_to(source_root.resolve()).as_posix(), False
    except ValueError:
        return cleaned, False


def scan_all_sources(source_records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    tables: list[dict[str, Any]] = []
    table_rows: list[dict[str, Any]] = []
    equations: list[dict[str, Any]] = []
    dependencies: list[dict[str, Any]] = []
    table_pattern = re.compile(r"\\begin\{table\*?\}(.*?)\\end\{table\*?\}", re.S)
    equation_pattern = re.compile(
        r"\\begin\{(?P<environment>equation|align|eqnarray|gather|multline)\*?\}"
        r"(?P<body>.*?)\\end\{(?P=environment)\*?\}", re.S,
    )
    macro_equation_pattern = re.compile(r"^\s*\\be\s*$\n(?P<body>.*?)^\s*\\ee\s*$", re.S | re.M)
    dependency_pattern = re.compile(r"\\(input|include)\s*\{([^}]+)\}")
    for source_record in source_records:
        source_root_text = source_record.get("local_source_root") or ""
        if not source_root_text:
            continue
        source_root = Path(source_root_text)
        if not source_root.is_dir():
            continue
        source_id = source_record["source_id"]
        arxiv_id = source_record["arxiv_id"]
        for tex_path in sorted(source_root.rglob("*.tex")):
            relative = tex_path.relative_to(source_root).as_posix()
            try:
                raw_text = tex_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            text = strip_comments(raw_text)
            for dependency in dependency_pattern.finditer(text):
                resolved, exists = resolve_dependency(source_root, tex_path, dependency.group(2))
                dependencies.append({
                    "source_id": source_id, "arxiv_id": arxiv_id, "source_path": relative,
                    "line": line_number(text, dependency.start()), "command": dependency.group(1),
                    "target_raw": dependency.group(2), "target_resolved": resolved, "exists": str(exists).lower(),
                })
            for ordinal, match in enumerate(table_pattern.finditer(text), 1):
                table_text = match.group(0)
                try:
                    rows = split_latex_rows(table_text)
                except ValueError:
                    rows = []
                table_caption = caption(table_text)
                label = table_label(table_text)
                identifier_seed = f"{source_id}:{relative}:{match.start()}"
                table_id = f"{source_id}-table-{hashlib.sha1(identifier_seed.encode()).hexdigest()[:12]}"
                offset_line = line_number(text, match.start()) - 1
                kind = classify_table(relative, table_caption, rows)
                tables.append({
                    "table_id": table_id, "source_id": source_id, "arxiv_id": arxiv_id,
                    "source_path": relative, "line_start": offset_line + 1,
                    "line_end": line_number(text, match.end()), "label": label, "caption": table_caption,
                    "column_count": max((len(row.cells) for row in rows), default=0), "row_count": len(rows),
                    "numeric_row_count": sum(numeric_cell_count(row.cells) > 0 for row in rows),
                    "candidate_kind": kind, "review_status": "structurally_extracted_unreviewed",
                })
                for row_index, row in enumerate(rows, 1):
                    table_rows.append({
                        "table_id": table_id, "source_id": source_id, "arxiv_id": arxiv_id,
                        "source_path": relative, "row_index": row_index,
                        "line_start": offset_line + row.line_start, "line_end": offset_line + row.line_end,
                        "cells_latex": row.cells, "raw_latex": row.raw,
                        "numeric_cell_count": numeric_cell_count(row.cells), "candidate_kind": kind,
                    })
            for match in equation_pattern.finditer(text):
                containing_line = text[text.rfind("\n", 0, match.start()) + 1:text.find("\n", match.start())]
                if "\\newcommand" in containing_line:
                    continue
                body = match.group("body").strip()
                label_match = re.search(r"\\label\{([^}]+)\}", body)
                label = label_match.group(1) if label_match else ""
                context_start = max(0, text.rfind("\n\n", 0, match.start()))
                context_end = text.find("\n\n", match.end())
                context_end = len(text) if context_end < 0 else context_end
                context = text[context_start:context_end].strip()
                empirical = bool(re.search(r"empirical|fit|regression|residual|coefficient|correlation", context, re.I))
                equations.append({
                    "source_id": source_id, "arxiv_id": arxiv_id, "source_path": relative,
                    "line_start": line_number(text, match.start()), "line_end": line_number(text, match.end()),
                    "label": label, "equation_latex": re.sub(r"\\label\{[^}]+\}", "", body).strip(),
                    "context_latex": context, "empirical_relation_candidate": empirical,
                    "review_status": "structurally_extracted_unreviewed",
                })
            for match in macro_equation_pattern.finditer(text):
                body = match.group("body").strip()
                label_match = re.search(r"\\label\{([^}]+)\}", body)
                label = label_match.group(1) if label_match else ""
                context_start = max(0, text.rfind("\n\n", 0, match.start()))
                context_end = text.find("\n\n", match.end())
                context_end = len(text) if context_end < 0 else context_end
                context = text[context_start:context_end].strip()
                equations.append({
                    "source_id": source_id, "arxiv_id": arxiv_id, "source_path": relative,
                    "line_start": line_number(text, match.start()), "line_end": line_number(text, match.end()),
                    "label": label, "equation_latex": re.sub(r"\\label\{[^}]+\}", "", body).strip(),
                    "context_latex": context,
                    "empirical_relation_candidate": bool(re.search(r"empirical|fit|regression|residual|coefficient|correlation", context, re.I)),
                    "review_status": "structurally_extracted_unreviewed",
                })
    # Some journals place only table rows in an included file. Promote those
    # dependency fragments to synthetic tables so their data are not lost.
    source_root_by_id = {row["source_id"]: Path(row["local_source_root"]) for row in source_records if row.get("local_source_root")}
    represented_paths = {(row["source_id"], row["source_path"]) for row in tables}
    seen_fragments: set[tuple[str, str]] = set()
    for dependency in dependencies:
        key = (dependency["source_id"], dependency["target_resolved"])
        if dependency["exists"] != "true" or key in represented_paths or key in seen_fragments:
            continue
        fragment_path = source_root_by_id[dependency["source_id"]] / dependency["target_resolved"]
        if fragment_path.suffix.lower() != ".tex":
            continue
        fragment = strip_comments(fragment_path.read_text(encoding="utf-8", errors="replace"))
        if "&" not in fragment or "\\\\" not in fragment:
            continue
        wrapper = "\\begin{tabular}{l}\n" + fragment + "\n\\end{tabular}"
        try:
            rows = split_latex_rows(wrapper)
        except ValueError:
            continue
        if not rows or max((len(row.cells) for row in rows), default=0) < 2:
            continue
        source_id = dependency["source_id"]
        relative = dependency["target_resolved"]
        identifier_seed = f"{source_id}:{relative}:included-fragment"
        table_id = f"{source_id}-table-{hashlib.sha1(identifier_seed.encode()).hexdigest()[:12]}"
        kind = classify_table(relative, "Included LaTeX table fragment", rows)
        tables.append({
            "table_id": table_id, "source_id": source_id, "arxiv_id": dependency["arxiv_id"],
            "source_path": relative, "line_start": 1, "line_end": fragment.count("\n") + 1,
            "label": f"included:{Path(relative).stem}", "caption": "Included LaTeX table fragment",
            "column_count": max(len(row.cells) for row in rows), "row_count": len(rows),
            "numeric_row_count": sum(numeric_cell_count(row.cells) > 0 for row in rows),
            "candidate_kind": kind, "review_status": "structurally_extracted_unreviewed",
        })
        for row_index, row in enumerate(rows, 1):
            table_rows.append({
                "table_id": table_id, "source_id": source_id, "arxiv_id": dependency["arxiv_id"],
                "source_path": relative, "row_index": row_index,
                "line_start": max(1, row.line_start - 1), "line_end": max(1, row.line_end - 1),
                "cells_latex": row.cells, "raw_latex": row.raw,
                "numeric_cell_count": numeric_cell_count(row.cells), "candidate_kind": kind,
            })
        seen_fragments.add(key)
    tables.sort(key=lambda row: (row["source_id"], row["source_path"], row["line_start"], row["table_id"]))
    table_rows.sort(key=lambda row: (row["source_id"], row["source_path"], row["line_start"], row["row_index"]))
    return tables, table_rows, equations, dependencies


def publication_exports(tables: list[dict[str, Any]], table_rows: list[dict[str, Any]],
                        equations: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Convert structural records into lossless, source-linked public CSV rows."""
    table_by_id = {row["table_id"]: row for row in tables}
    cells: list[dict[str, Any]] = []
    for row in table_rows:
        table = table_by_id[row["table_id"]]
        for column_index, value in enumerate(row["cells_latex"], 1):
            cells.append({
                "cell_id": f'{row["table_id"]}-r{row["row_index"]:04d}-c{column_index:03d}',
                "table_id": row["table_id"], "source_id": row["source_id"],
                "source_path": row["source_path"], "table_label": table["label"],
                "row_index": row["row_index"], "column_index": column_index,
                "line_start": row["line_start"], "line_end": row["line_end"],
                "value_latex": value, "value_text": clean_latex(value),
                "numeric_value": central_number(value), "candidate_kind": row["candidate_kind"],
                "review_status": "lossless_structural_extraction",
            })
    public_equations = []
    for equation in equations:
        seed = ":".join(str(equation[key]) for key in ("source_id", "source_path", "line_start"))
        public_equations.append({
            **equation, "equation_id": f'{equation["source_id"]}-equation-{hashlib.sha1(seed.encode()).hexdigest()[:12]}',
        })
    return cells, public_equations


def indexed_tables(tables: list[dict[str, Any]], table_rows: list[dict[str, Any]]) -> dict[tuple[str, str], tuple[dict[str, Any], list[dict[str, Any]]]]:
    by_id: dict[str, list[dict[str, Any]]] = {}
    for row in table_rows:
        by_id.setdefault(row["table_id"], []).append(row)
    return {(table["source_id"], table["label"]): (table, by_id.get(table["table_id"], [])) for table in tables}


def clean_eos(value: str) -> str:
    value = re.sub(r"\\cite\{[^}]*\}", "", value)
    value = re.sub(r"\$?\+?\\Gamma.*$", "", value)
    return clean_latex(value).strip()


def model_key(value: str) -> str:
    return stable_id(re.sub(r"\\[A-Za-z]+", "", value).replace("$", "").replace("{", "").replace("}", ""))


def base_waveform(source_id: str, catalogue: str, simulation_id: str, eos_name: str,
                  m1: float, m2: float, source_path: str, notes: str = "") -> dict[str, Any]:
    identifier = f"{source_id}-{stable_id(catalogue, simulation_id or eos_name, str(m1), str(m2))}"
    return {
        "id": identifier, "source_id": source_id, "catalogue": catalogue,
        "simulation_id": simulation_id, "eos": eos_name, "eos_variant": "",
        "m1_msun": m1, "m2_msun": m2, "mtot_msun": m1 + m2,
        "mchirp_msun": chirp_mass(m1, m2), "q": min(m1, m2) / max(m1, m2),
        "q_definition": "min(m1,m2)/max(m1,m2) <= 1", "q_original": "",
        "q_original_definition": "", "lambda1": "", "lambda2": "", "lambda_tilde": "",
        "f_peak_khz": "", "f_2_0_khz": "", "f_2_0_status": "not_reported",
        "f_spiral_khz": "", "f_spiral_status": "not_reported", "f_radial_khz": "",
        "f_peak_early_khz": "", "f_peak_late_khz": "", "f_peak_mean_khz": "",
        "f_peak_instantaneous_khz": "", "f_merger_khz": "", "f_gw_initial_hz": "",
        "spectral_type": "unknown", "simulation_code": "", "numerical_method": "",
        "waveform_extraction": "", "source_table": source_path, "notes": notes,
    }


def append_provenance(provenance: list[dict[str, Any]], record_type: str, record_id: str,
                      source_id: str, table: dict[str, Any], row: dict[str, Any]) -> None:
    provenance.append({
        "record_type": record_type, "record_id": record_id, "source_id": source_id,
        "source_path": row["source_path"], "source_line_start": row["line_start"],
        "source_line_end": row["line_end"], "table_label": table["label"],
        "raw_latex": row["raw_latex"], "extraction_method": "reviewed_paper_table_adapter",
        "review_status": "verified",
    })


def extract_additional_papers(tables: list[dict[str, Any]], table_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Normalize reviewed simulation tables that map safely to the public schema."""
    lookup = indexed_tables(tables, table_rows)
    waveforms: list[dict[str, Any]] = []
    eos_records: list[dict[str, Any]] = []
    extras: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []

    def extra(waveform: dict[str, Any], table: dict[str, Any], row: dict[str, Any], quantity: str,
              value_text: str, unit: str, status: str = "measured") -> None:
        value = central_number(value_text)
        extras.append({
            "measurement_id": f'{waveform["id"]}-{stable_id(quantity)}', "waveform_id": waveform["id"],
            "source_id": waveform["source_id"], "simulation_id": waveform["simulation_id"],
            "quantity": quantity, "value": value, "unit": unit, "uncertainty_plus": "",
            "uncertainty_minus": "", "value_text": value_text, "status": status,
            "source_path": row["source_path"], "table_label": table["label"],
            "line_start": row["line_start"], "notes": "Original table cell retained in value_text.",
        })

    # Bauswein & Janka (2012): every model is explicitly a 1.35+1.35 Msun binary.
    table, rows = lookup[("arxiv-1106-1616", "tab:models")]
    for row in rows:
        cells = row["cells_latex"]
        if len(cells) != 5 or central_number(cells[1]) is None:
            continue
        eos_name = clean_eos(cells[0])
        waveform = base_waveform("arxiv-1106-1616", "Bauswein2012", eos_name, eos_name, 1.35, 1.35, row["source_path"])
        peak_parts = [part.strip() for part in cells[3].split(",")]
        waveform["f_peak_khz"] = central_number(peak_parts[0])
        waveform["notes"] = "Prompt collapse." if waveform["f_peak_khz"] is None else "Equal-mass setup stated in the article text."
        waveforms.append(waveform)
        append_provenance(provenance, "waveform", waveform["id"], waveform["source_id"], table, row)
        eos_id = f'arxiv-1106-1616-eos-{stable_id(eos_name)}'
        eos_records.append({
            "id": eos_id, "source_id": "arxiv-1106-1616", "eos": eos_name, "eos_variant": "",
            "r_1_2_km": "", "r_1_4_km": "", "r_1_6_km": "", "r_1_8_km": "",
            "m_tov_msun": central_number(cells[1]), "definition_notes": f'Maximum-mass radius Rmax={central_number(cells[2])} km.',
            "source_table": row["source_path"],
        })
        append_provenance(provenance, "eos", eos_id, "arxiv-1106-1616", table, row)
        extra(waveform, table, row, "f_peak_fwhm", peak_parts[1] if len(peak_parts) > 1 else "", "kHz",
              "measured" if len(peak_parts) > 1 else "prompt_collapse")
        extra(waveform, table, row, "effective_peak_amplitude_20mpc", cells[4], "1e-21",
              "measured" if central_number(cells[4]) is not None else "prompt_collapse")

    # Bernuzzi, Dietrich & Nagar (2015): f2 is explicitly the main postmerger peak.
    table, rows = lookup[("arxiv-1504-01764", "tab:conf")]
    for row in rows:
        cells = row["cells_latex"]
        if len(cells) != 7 or central_number(cells[2]) is None:
            continue
        total_mass, q_source = central_number(cells[2]), central_number(cells[3])
        m_high, m_low = total_mass * q_source / (1 + q_source), total_mass / (1 + q_source)
        waveform = base_waveform("arxiv-1504-01764", "Bernuzzi2015", clean_latex(cells[0]), clean_eos(cells[1]), m_high, m_low, row["source_path"])
        waveform.update({
            "q_original": q_source, "q_original_definition": "M_A/M_B >= 1",
            "f_peak_khz": central_number(cells[4]),
            "notes": "The paper defines f2 as the main postmerger spectral peak; mapped to canonical f_peak.",
        })
        waveforms.append(waveform)
        append_provenance(provenance, "waveform", waveform["id"], waveform["source_id"], table, row)
        extra(waveform, table, row, "M_f_2", cells[5], "1e-2")
        extra(waveform, table, row, "kappa_2_T", cells[6], "dimensionless")

    # Kiuchi et al. (2020): the table's f_peak is a merger-time frequency,
    # while f2 is explicitly the dominant postmerger spectral frequency.
    table, rows = lookup[("arxiv-1907-03790", "tb:fpeak")]
    model_table, model_rows = lookup[("arxiv-1907-03790", "tb:model")]
    models = {clean_latex(row["cells_latex"][0]).lstrip("\\"): row for row in model_rows if len(row["cells_latex"]) == 11}
    for row in rows:
        cells = row["cells_latex"]
        if len(cells) != 10 or central_number(cells[2]) is None:
            continue
        simulation_id = clean_latex(cells[0]).lstrip("\\").strip()
        match = re.search(r"^(.*?)(\d{3})-(\d{3})$", simulation_id)
        if not match:
            continue
        eos_name, m1, m2 = match.group(1), int(match.group(2)) / 100, int(match.group(3)) / 100
        waveform = base_waveform("arxiv-1907-03790", "Kiuchi2020", simulation_id, eos_name, m1, m2, row["source_path"])
        f2_hz = central_number(cells[4])
        waveform.update({
            "f_peak_khz": f2_hz / 1000 if f2_hz is not None else "",
            "f_merger_khz": central_number(cells[2]) / 1000,
            "notes": "Original f_peak is the merger-time frequency and is retained as f_merger; original f2 is the dominant postmerger spectral peak.",
        })
        model = models.get(simulation_id)
        if model:
            waveform["lambda_tilde"] = central_number(model["cells_latex"][7])
            waveform["mchirp_msun"] = central_number(model["cells_latex"][5])
        waveforms.append(waveform)
        append_provenance(provenance, "waveform", waveform["id"], waveform["source_id"], table, row)
        extra(waveform, table, row, "f_merger", cells[2], "Hz")
        extra(waveform, table, row, "f_2", cells[4], "Hz", "measured" if f2_hz is not None else "not_reported")
        extra(waveform, table, row, "lambda_tilde_one_fifth", cells[1], "dimensionless")

    table, rows = lookup[("arxiv-1907-03790", "tb:eos_model")]
    for row in rows:
        cells = row["cells_latex"]
        if len(cells) != 12 or central_number(cells[1]) is None:
            continue
        eos_name = clean_eos(cells[0])
        eos_id = f'arxiv-1907-03790-eos-{stable_id(eos_name)}'
        eos_records.append({
            "id": eos_id, "source_id": "arxiv-1907-03790", "eos": eos_name, "eos_variant": "",
            "r_1_2_km": "", "r_1_4_km": "", "r_1_6_km": "", "r_1_8_km": "",
            "m_tov_msun": central_number(cells[11]),
            "definition_notes": f'Published radii include R_1.35={central_number(cells[6])} km; full mass grid remains in published_table_cells.csv.',
            "source_table": row["source_path"],
        })
        append_provenance(provenance, "eos", eos_id, "arxiv-1907-03790", table, row)

    # Takami, Rezzolla & Baiotti (2015) and Rezzolla & Takami (2016): join model
    # parameters and spectral measurements by the published simulation identifier.
    for source_id, catalogue, frequency_unit in (
        ("arxiv-1412-3240", "Takami2015", "Hz"),
        ("arxiv-1604-00246", "RezzollaTakami2016", "kHz"),
    ):
        model_table, model_rows = lookup[(source_id, "tab:models")]
        frequency_table, frequency_rows = lookup[(source_id, "tab:SNRs")]
        frequency_by_model = {
            model_key(row["cells_latex"][0]): row for row in frequency_rows
            if len(row["cells_latex"]) >= 5 and central_number(row["cells_latex"][1]) is not None
        }
        for row in model_rows:
            cells = row["cells_latex"]
            if len(cells) < 14 or central_number(cells[2]) is None:
                continue
            key = model_key(cells[0])
            frequency_row = frequency_by_model.get(key)
            if frequency_row is None:
                continue
            q_source, average = central_number(cells[2]), central_number(cells[3])
            m_high, m_low = 2 * average / (1 + q_source), 2 * average * q_source / (1 + q_source)
            waveform = base_waveform(source_id, catalogue, key, clean_eos(cells[1]), m_high, m_low, row["source_path"])
            frequency_cells = frequency_row["cells_latex"]
            scale = 0.001 if frequency_unit == "Hz" else 1.0
            f2_index = 3 if source_id == "arxiv-1412-3240" else 4
            f2_value = central_number(frequency_cells[f2_index])
            waveform.update({
                "q_original": q_source, "q_original_definition": "smaller/larger component mass <= 1",
                "f_peak_khz": f2_value * scale if f2_value is not None else "",
                "f_gw_initial_hz": central_number(cells[8]),
                "notes": "Model and spectral tables joined by the published simulation identifier; f1 is retained separately and is not relabeled f2-0.",
            })
            if source_id == "arxiv-1412-3240":
                waveform["f_merger_khz"] = central_number(frequency_cells[1]) / 1000
            else:
                waveform["f_merger_khz"] = central_number(frequency_cells[1])
                waveform["f_peak_early_khz"] = central_number(frequency_cells[3])
            waveforms.append(waveform)
            append_provenance(provenance, "waveform", waveform["id"], source_id, model_table, row)
            quantities = (("f_max", 1), ("f_1", 2), ("f_2", f2_index))
            if source_id == "arxiv-1604-00246":
                quantities += (("f_2_initial", 3), ("f_m0", 5))
            for quantity, column in quantities:
                extra(waveform, frequency_table, frequency_row, quantity, frequency_cells[column], frequency_unit)

    # Clark et al. (2016): source-specific R_1.35 EOS values.
    table, rows = lookup[("arxiv-1509-08522", "tab1")]
    for row in rows:
        cells = row["cells_latex"]
        if len(cells) != 3 or central_number(cells[2]) is None:
            continue
        eos_name = clean_eos(cells[0])
        eos_id = f'arxiv-1509-08522-eos-{stable_id(eos_name)}'
        eos_records.append({
            "id": eos_id, "source_id": "arxiv-1509-08522", "eos": eos_name, "eos_variant": "",
            "r_1_2_km": "", "r_1_4_km": "", "r_1_6_km": "", "r_1_8_km": "",
            "m_tov_msun": "", "definition_notes": f'Published R_1.35={central_number(cells[2])} km.',
            "source_table": row["source_path"],
        })
        append_provenance(provenance, "eos", eos_id, "arxiv-1509-08522", table, row)

    # Breschi et al. (2019): validation binaries with published NR f2 values.
    table, rows = lookup[("arxiv-1908-11418", "tab:valbns")]
    for index, row in enumerate(rows, 1):
        cells = row["cells_latex"]
        if len(cells) < 7 or central_number(cells[3]) is None:
            continue
        m1, m2 = central_number(cells[3]), central_number(cells[4])
        eos_name = clean_eos(cells[0])
        waveform = base_waveform("arxiv-1908-11418", "NRPM-validation", f"validation-{index:02d}", eos_name, m1, m2, row["source_path"])
        waveform["f_peak_khz"] = central_number(cells[6])
        waveform["lambda_tilde"] = central_number(cells[5])
        waveform["notes"] = "Published validation binary; an empty f2 denotes no reported postmerger peak."
        waveforms.append(waveform)
        append_provenance(provenance, "waveform", waveform["id"], waveform["source_id"], table, row)

    # Prakash et al. (2024): NR simulation configurations and collapse outcomes.
    table, rows = lookup[("arxiv-2310-06025", "tab:NR_Simulation_Summary")]
    for index, row in enumerate(rows, 1):
        cells = row["cells_latex"]
        if len(cells) != 7 or central_number(cells[1]) is None:
            continue
        m1, m2 = central_number(cells[1]), central_number(cells[2])
        waveform = base_waveform("arxiv-2310-06025", "Prakash2024-NR", f"nr-{index:02d}", clean_eos(cells[0]), m1, m2, row["source_path"])
        waveform.update({"q_original": central_number(cells[3]), "q_original_definition": "m1/m2 >= 1", "lambda1": central_number(cells[4]), "lambda2": central_number(cells[5]), "notes": f"Collapse outcome/time: {clean_latex(cells[6])}."})
        waveforms.append(waveform)
        append_provenance(provenance, "waveform", waveform["id"], waveform["source_id"], table, row)
        extra(waveform, table, row, "collapse_time", cells[6], "ms", "lower_bound_or_stable" if "HMNS" in cells[6] else "measured")

    # Bamber et al. (2025): magnetic-field variants with five frequency measurements.
    table, rows = lookup[("arxiv-2411-00943", "tab:GW_freqs")]
    for index, row in enumerate(rows, 1):
        cells = row["cells_latex"]
        if len(cells) != 8 or central_number(cells[1]) is None:
            continue
        total_mass = central_number(cells[1])
        magnetic_variant = clean_latex(cells[2])
        simulation_id = f'{clean_eos(cells[0])}-{total_mass:.2f}-{stable_id(magnetic_variant or "hydro")}'
        waveform = base_waveform("arxiv-2411-00943", "Bamber2025", simulation_id, clean_eos(cells[0]), total_mass / 2, total_mass / 2, row["source_path"])
        waveform.update({
            "f_peak_khz": central_number(cells[3]), "f_2_0_khz": central_number(cells[4]),
            "f_2_0_status": "measured", "f_spiral_khz": central_number(cells[6]),
            "f_spiral_status": "measured", "f_radial_khz": central_number(cells[7]),
            "notes": f"Initial magnetic-field configuration: {magnetic_variant or '0'}. Frequencies include parenthetical last-digit uncertainties.",
        })
        waveforms.append(waveform)
        append_provenance(provenance, "waveform", waveform["id"], waveform["source_id"], table, row)
        for quantity, cell in zip(("f_2", "f_2_minus_0", "f_2_plus_0", "f_spiral", "f_0"), cells[3:8]):
            extra(waveform, table, row, quantity, cell, "kHz")

    # Vretinaris et al. (2026): explicitly listed waveform labels, q, and average component mass.
    table, rows = lookup[("arxiv-2501-11518", "table:info")]
    for row in rows:
        cells = row["cells_latex"]
        if len(cells) != 5 or central_number(cells[2]) is None:
            continue
        q_source, average = central_number(cells[2]), central_number(cells[3])
        m_high, m_low = 2 * average * q_source / (1 + q_source), 2 * average / (1 + q_source)
        waveform = base_waveform("arxiv-2501-11518", "Vretinaris2026", clean_latex(cells[0]), clean_eos(cells[1]), m_high, m_low, row["source_path"])
        waveform.update({"q_original": q_source, "q_original_definition": "larger/smaller component mass >= 1", "notes": "Component masses derived from the published average mass and mass ratio."})
        waveforms.append(waveform)
        append_provenance(provenance, "waveform", waveform["id"], waveform["source_id"], table, row)

    # Grippa et al. (2025): strange-star thermal-treatment and resolution variants.
    table, rows = lookup[("arxiv-2407-11143", "Table:summary")]
    for index, row in enumerate(rows, 1):
        cells = row["cells_latex"]
        if len(cells) != 9 or "EOS" in cells[0] or central_number(cells[1]) is None:
            continue
        variant = clean_latex(cells[0])
        resolution = clean_latex(cells[5])
        waveform = base_waveform("arxiv-2407-11143", "Grippa2025", f"strange-star-{stable_id(variant, resolution)}", "strange-star", central_number(cells[1]), central_number(cells[2]), row["source_path"])
        waveform.update({
            "eos_variant": variant, "lambda_tilde": central_number(cells[4]),
            "f_peak_khz": central_number(cells[6]),
            "notes": f"Thermal treatment: {variant}; resolution: {resolution}; collapse: {clean_latex(cells[7])}.",
        })
        waveforms.append(waveform)
        append_provenance(provenance, "waveform", waveform["id"], waveform["source_id"], table, row)
        extra(waveform, table, row, "collapse_time_after_merger", cells[8], "ms",
              "measured" if central_number(cells[8]) is not None else "no_collapse")

    # Huang & Baiotti (2026): equal-mass models and four separately defined frequencies.
    table, rows = lookup[("arxiv-2606-08522", "tab:allmodels")]
    for row in rows:
        cells = row["cells_latex"]
        if len(cells) != 11 or clean_latex(cells[0]).lower().startswith("model"):
            continue
        simulation_id = clean_latex(cells[0]).replace("[-0.5em]", "").replace("[0.5em]", "").strip()
        mass = central_number(cells[1])
        mass_match = re.search(r"M(\d{3})", simulation_id, re.I)
        if mass is None and mass_match:
            mass = int(mass_match.group(1)) / 100
        if mass is None:
            continue
        eos_name = "soft" if "soft" in simulation_id.lower() else "stiff"
        waveform = base_waveform("arxiv-2606-08522", "Huang2026", simulation_id, eos_name, mass, mass, row["source_path"])
        waveform.update({"eos_variant": simulation_id, "lambda1": central_number(cells[5]), "lambda2": central_number(cells[5]), "f_peak_mean_khz": (central_number(cells[9]) / 1000 if central_number(cells[9]) is not None else ""), "f_radial_khz": (central_number(cells[7]) / 1000 if central_number(cells[7]) is not None else ""), "notes": "The reported f2 is a time-mean frequency and is not put in f_peak_khz; f1 and f3 are not automatically identified with f_spiral or f2-0."})
        waveforms.append(waveform)
        append_provenance(provenance, "waveform", waveform["id"], waveform["source_id"], table, row)
        for quantity, cell in zip(("f_contact", "f_0", "f_1", "f_2_mean", "f_3"), cells[6:11]):
            extra(waveform, table, row, quantity, cell, "Hz", "measured" if central_number(cell) is not None else "not_identified")

    return waveforms, eos_records, extras, provenance


def extract_additional_relations(tables: list[dict[str, Any]], table_rows: list[dict[str, Any]],
                                 equations: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Normalize reviewed coefficient/formula tables outside the reference paper."""
    lookup = indexed_tables(tables, table_rows)
    relations: list[dict[str, Any]] = []
    coefficients: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []

    # Bernuzzi, Dietrich & Nagar (2015), rational-polynomial tidal fits.
    table, rows = lookup[("arxiv-1504-01764", "tab:fit_coefs")]
    for ordinal, row in enumerate(rows, 1):
        cells = row["cells_latex"]
        if len(cells) != 5 or cells[0].lstrip().startswith("$Q(") or central_number(cells[1]) is None:
            continue
        observable = clean_latex(cells[0])
        relation_id = f'arxiv-1504-01764-kappa2t-{stable_id(observable, str(ordinal))}'
        relations.append({
            "relation_id": relation_id, "source_id": "arxiv-1504-01764",
            "family": "tidal_coupling_rational_fit", "equation_label": "fitmodel",
            "equation_latex": r"Q(\kappa_2^T)=Q_0[1+n_1\kappa_2^T+n_2(\kappa_2^T)^2]/[1+d_1\kappa_2^T]",
            "dependent_variable": "M*f_peak" if "f_2" in cells[0] else observable,
            "dependent_unit": "dimensionless", "independent_variables": "kappa_2_T",
            "calibration_population": "99 BNS data points for the postmerger f2 fit",
            "applicability": "M=2.45--2.9 Msun; q=1.0--1.5 for the postmerger dataset",
            "source_table": table["label"], "source_path": row["source_path"],
            "r_squared_adjusted": "", "max_residual": "", "mean_residual": "",
            "residual_std": "", "residual_unit": "", "review_status": "verified_from_coefficient_table",
            "notes": "Original observable retained; f2 is explicitly the main postmerger peak. Header scale factors have been applied to coefficients.",
        })
        for name, term, cell, scale in zip(("Q0", "n1", "n2", "d1"), ("normalization", "kappa_2_T", "kappa_2_T^2", "denominator_kappa_2_T"), cells[1:], (1, 1e-2, 1e-5, 1e-2)):
            coefficients.append({"relation_id": relation_id, "coefficient": name, "term": term,
                                 "value": central_number(cell) * scale, "source_id": "arxiv-1504-01764", "source_path": row["source_path"]})
        append_provenance(provenance, "relation", relation_id, "arxiv-1504-01764", table, row)

    # Kiuchi et al. (2020): keep merger f_peak distinct from postmerger f2.
    kiuchi_specs = {
        "eq:fpeak": ("f_merger_hz", "merger_frequency_from_tidal_deformability", [("a00", "a0 constant", 4.536), ("a01", "a0 eta", -1.230), ("a10", "a1 constant", -0.929), ("a11", "a1 eta", 3.120)]),
        "eq:f2": ("f_peak_hz", "postmerger_frequency_from_tidal_deformability", [("c00", "c0 constant", 11.363), ("c01", "c0 eta", -27.418), ("c10", "c1 constant", -2.158), ("c11", "c1 eta", 7.941)]),
    }
    for equation in equations:
        if equation["source_id"] != "arxiv-1907-03790" or equation["label"] not in kiuchi_specs:
            continue
        dependent, family, coefficient_specs = kiuchi_specs[equation["label"]]
        relation_id = f'arxiv-1907-03790-{stable_id(equation["label"])}'
        relations.append({
            "relation_id": relation_id, "source_id": "arxiv-1907-03790", "family": family,
            "equation_label": equation["label"], "equation_latex": equation["equation_latex"],
            "dependent_variable": dependent, "dependent_unit": "Hz",
            "independent_variables": "eta;lambda_tilde^(1/5);total_mass_msun",
            "calibration_population": "Kiuchi et al. BNS simulations", "applicability": "Source calibration domain",
            "source_table": "", "source_path": equation["source_path"], "r_squared_adjusted": "",
            "max_residual": "", "mean_residual": "", "residual_std": "", "residual_unit": "",
            "review_status": "verified_from_equation_and_context",
            "notes": "The source's f_peak denotes merger frequency; its f2 denotes the dominant postmerger spectral peak.",
        })
        for name, term, value in coefficient_specs:
            coefficients.append({"relation_id": relation_id, "coefficient": name, "term": term,
                                 "value": value, "source_id": "arxiv-1907-03790", "source_path": equation["source_path"]})
        provenance.append({"record_type": "relation", "record_id": relation_id, "source_id": "arxiv-1907-03790",
                           "source_path": equation["source_path"], "source_line_start": equation["line_start"],
                           "source_line_end": equation["line_end"], "table_label": equation["label"],
                           "raw_latex": equation["equation_latex"], "extraction_method": "reviewed_equation_adapter",
                           "review_status": "verified"})

    # Vretinaris et al. (2026): new f_2-0 and f_spiral relations calibrated
    # from the Vretinaris, Stergioulas & Bauswein (2020) simulation data.
    vretinaris_2026_specs = {
        "eq:quasiradial": ("f_2_0_khz", "secondary_frequency_from_tidal_deformability",
                           0.362, 0.941, (("b0", "1", 0.558), ("b1", "mchirp_msun", -0.406), ("b2", "lambda_tilde^(-1/2)", 48.696))),
        "eq:spiral": ("f_spiral_khz", "spiral_frequency_from_tidal_deformability",
                      0.461, 0.944, (("b0", "1", 1.2), ("b1", "mchirp_msun", -0.442), ("b2", "lambda_tilde^(-1/2)", 45.819))),
    }
    for equation in equations:
        if equation["source_id"] != "arxiv-2501-11518" or equation["label"] not in vretinaris_2026_specs:
            continue
        dependent, family, maximum_residual, r_squared, terms = vretinaris_2026_specs[equation["label"]]
        relation_id = f'arxiv-2501-11518-{stable_id(equation["label"])}'
        relations.append({
            "relation_id": relation_id, "source_id": "arxiv-2501-11518", "family": family,
            "equation_label": equation["label"], "equation_latex": equation["equation_latex"],
            "dependent_variable": dependent, "dependent_unit": "kHz",
            "independent_variables": "mchirp_msun;lambda_tilde",
            "calibration_population": "Vretinaris, Stergioulas & Bauswein (2020) Table II data",
            "applicability": "Source calibration domain; equal- and unequal-mass BNS models",
            "source_table": "", "source_path": equation["source_path"],
            "r_squared_adjusted": r_squared, "max_residual": maximum_residual,
            "mean_residual": "", "residual_std": "", "residual_unit": "kHz",
            "review_status": "verified_from_equation_and_context",
            "notes": "The published expression fits f*M_chirp; divide its right-hand side by M_chirp to obtain the frequency in kHz.",
        })
        for name, term, value in terms:
            coefficients.append({"relation_id": relation_id, "coefficient": name, "term": term,
                                 "value": value, "source_id": "arxiv-2501-11518", "source_path": equation["source_path"]})
        provenance.append({
            "record_type": "relation", "record_id": relation_id, "source_id": "arxiv-2501-11518",
            "source_path": equation["source_path"], "source_line_start": equation["line_start"],
            "source_line_end": equation["line_end"], "table_label": equation["label"],
            "raw_latex": equation["equation_latex"], "extraction_method": "reviewed_equation_adapter",
            "review_status": "verified",
        })

    # Topolski, Tootle & Rezzolla (2023), F1 frequency fits.
    table, rows = lookup[("arxiv-2310-10728", "tab:fit_parameters")]
    for ordinal, row in enumerate(rows, 1):
        cells = row["cells_latex"]
        if len(cells) != 11 or "Freq." in cells[0] or central_number(cells[1]) is None:
            continue
        original = cells[0]
        dependent = "f_peak_hz" if "f_{2}" in original else ("f_peak_instantaneous_hz" if "_{0}" in original else "f_merger_hz")
        relation_id = f'arxiv-2310-10728-f1-{ordinal:02d}'
        relations.append({
            "relation_id": relation_id, "source_id": "arxiv-2310-10728", "family": "F1_tidal_mass_ratio_frequency_fit",
            "equation_label": "F1", "equation_latex": r"log10[(M/Msun)(f/Hz)] = a0 + (b0+b1*q+b2*q^2)(kappa_2_T)^n",
            "dependent_variable": dependent, "dependent_unit": "Hz", "independent_variables": "total_mass_msun;q;kappa_2_T",
            "calibration_population": "118 irrotational BNS simulations", "applicability": "Source calibration domain",
            "source_table": table["label"], "source_path": row["source_path"],
            "r_squared_adjusted": central_number(cells[10]), "max_residual": central_number(cells[7]),
            "mean_residual": central_number(cells[6]), "residual_std": "", "residual_unit": "percent",
            "review_status": "verified_from_coefficient_table",
            "notes": f"Original dependent symbol: {clean_latex(original)}; dagger marks n optimized by the fit.",
        })
        for name, term, cell in zip(("a0", "b0", "b1", "b2", "n"), ("constant", "kappa term constant", "kappa term q", "kappa term q^2", "kappa exponent"), cells[1:6]):
            coefficients.append({"relation_id": relation_id, "coefficient": name, "term": term,
                                 "value": central_number(cell), "source_id": "arxiv-2310-10728", "source_path": row["source_path"]})
        append_provenance(provenance, "relation", relation_id, "arxiv-2310-10728", table, row)

    table, rows = lookup[("arxiv-2102-12455", "Fit_table_Mergers")]
    for ordinal, row in enumerate(rows, 1):
        cells = row["cells_latex"]
        if len(cells) != 5 or "f_{\\mathrm{peak}}" not in cells[2]:
            continue
        population = clean_latex(cells[0])
        independent = clean_latex(cells[1])
        relation_id = f'arxiv-2102-12455-fpeak-{stable_id(population, independent, str(ordinal))}'
        relations.append({
            "relation_id": relation_id, "source_id": "arxiv-2102-12455",
            "family": "fixed_mass_peak_frequency", "equation_label": "Fit_table_Mergers",
            "equation_latex": cells[2], "dependent_variable": "f_peak_khz",
            "dependent_unit": "kHz", "independent_variables": independent,
            "calibration_population": population, "applicability": f"Binary component masses {population} Msun",
            "source_table": table["label"], "source_path": row["source_path"],
            "r_squared_adjusted": "", "max_residual": central_number(cells[4]),
            "mean_residual": central_number(cells[3]), "residual_std": "", "residual_unit": "Hz",
            "review_status": "verified_from_coefficient_table",
            "notes": "Equation and mean/maximum deviations transcribed from the published merger-fit table.",
        })
        append_provenance(provenance, "relation", relation_id, "arxiv-2102-12455", table, row)
    return relations, coefficients, provenance


def complete_eos_registry(waveforms: list[dict[str, Any]], eos: list[dict[str, Any]],
                          eos_provenance: list[dict[str, Any]], waveform_provenance: list[dict[str, Any]]) -> None:
    existing = {row["eos"].upper() for row in eos}
    provenance_by_waveform = {row["record_id"]: row for row in waveform_provenance}
    for waveform in waveforms:
        name = waveform["eos"].upper()
        if name in existing:
            continue
        record_id = f"{SOURCE_ID}-eos-{name.lower()}"
        eos.append({
            "id": record_id, "source_id": SOURCE_ID, "eos": name, "eos_variant": "",
            "r_1_2_km": "", "r_1_4_km": "", "r_1_6_km": "", "r_1_8_km": "",
            "m_tov_msun": "", "definition_notes": "EOS appears in the waveform table but has no row in tables/TOV_info.tex; properties remain missing.",
            "source_table": waveform["source_table"],
        })
        evidence = provenance_by_waveform[waveform["id"]]
        eos_provenance.append({**evidence, "record_type": "eos", "record_id": record_id})
        existing.add(name)


def retain_frequency_records(waveforms: list[dict[str, Any]], measurements_extra: list[dict[str, Any]],
                             provenance: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Keep normalized waveform rows only when at least one frequency is reported."""
    retained = [row for row in waveforms if any(row.get(field) not in (None, "") for field in FREQUENCY_FIELDS)]
    retained_ids = {row["id"] for row in retained}
    measurements_extra = [row for row in measurements_extra if row["waveform_id"] in retained_ids]
    provenance = [row for row in provenance
                  if row["record_type"] != "waveform" or row["record_id"] in retained_ids]
    return retained, measurements_extra, provenance


def complete_collection_eos_registry(waveforms: list[dict[str, Any]], eos: list[dict[str, Any]],
                                     provenance: list[dict[str, Any]]) -> None:
    """Ensure each source-specific waveform EOS resolves without merging definitions across papers."""
    existing = {(row["source_id"], row["eos"].upper()) for row in eos}
    evidence = {row["record_id"]: row for row in provenance if row["record_type"] == "waveform"}
    for waveform in waveforms:
        key = (waveform["source_id"], waveform["eos"].upper())
        if key in existing:
            continue
        record_id = f'{waveform["source_id"]}-eos-{stable_id(waveform["eos"])}'
        eos.append({
            "id": record_id, "source_id": waveform["source_id"], "eos": waveform["eos"],
            "eos_variant": waveform.get("eos_variant", ""), "r_1_2_km": "", "r_1_4_km": "",
            "r_1_6_km": "", "r_1_8_km": "", "m_tov_msun": "",
            "definition_notes": "EOS identifier is reported by this paper; no compatible stellar-property row was published in the adapted table.",
            "source_table": waveform["source_table"],
        })
        if waveform["id"] in evidence:
            provenance.append({**evidence[waveform["id"]], "record_type": "eos", "record_id": record_id})
        existing.add(key)


def extraction_coverage(sources: list[dict[str, Any]], tables: list[dict[str, Any]],
                        table_rows: list[dict[str, Any]], equations: list[dict[str, Any]],
                        dependencies: list[dict[str, Any]], waveforms: list[dict[str, Any]],
                        eos: list[dict[str, Any]], relations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    adapter_names = {
        SOURCE_ID: "vretinaris2020", "arxiv-1106-1616": "bauswein2012",
        "arxiv-1504-01764": "bernuzzi2015", "arxiv-1907-03790": "kiuchi2020",
        "arxiv-1412-3240": "takami2015", "arxiv-1509-08522": "clark2016",
        "arxiv-1604-00246": "rezzolla_takami2016",
        "arxiv-1908-11418": "breschi2019", "arxiv-2310-06025": "prakash2024",
        "arxiv-2102-12455": "lioutas2021",
        "arxiv-2310-10728": "topolski2023", "arxiv-2407-11143": "grippa2025",
        "arxiv-2411-00943": "bamber2025", "arxiv-2501-11518": "vretinaris2026",
        "arxiv-2606-08522": "huang2026",
    }
    for source in sources:
        source_id = source["source_id"]
        source_tables = [row for row in tables if row["source_id"] == source_id]
        source_equations = [row for row in equations if row["source_id"] == source_id]
        adapter = adapter_names.get(source_id, "")
        output.append({
            "source_id": source_id, "arxiv_id": source["arxiv_id"], "title": source["title"],
            "structural_status": "scanned",
            "tables": len(source_tables),
            "table_rows": sum(row["source_id"] == source_id for row in table_rows),
            "equations": len(source_equations),
            "empirical_equation_candidates": sum(bool(row["empirical_relation_candidate"]) for row in source_equations),
            "dependencies": sum(row["source_id"] == source_id for row in dependencies),
            "reviewed_adapter": adapter,
            "public_waveforms": sum(row["source_id"] == source_id for row in waveforms),
            "public_eos": sum(row["source_id"] == source_id for row in eos),
            "public_relations": sum(row["source_id"] == source_id for row in relations),
            "scientific_review_status": "normalized_table_adapter" if adapter else "lossless_structural_extraction",
            "notes": ("Reviewed table data promoted to normalized CSVs."
                      if adapter else "All detected table cells and equation environments are published losslessly with provenance; paper-specific semantic normalization remains extensible."),
        })
    return output


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: format_value(row.get(key)) for key in fieldnames})
    temporary.replace(path)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    with temporary.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    temporary.replace(path)


def validate(waveforms: list[dict[str, Any]], eos: list[dict[str, Any]], relations: list[dict[str, Any]],
             coefficients: list[dict[str, Any]], provenance: list[dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, severity: str = "error", detail: str = "") -> None:
        checks.append({"name": name, "status": "pass" if passed else severity, "detail": detail})

    reference_waveforms = [row for row in waveforms if row["source_id"] == SOURCE_ID]
    reference_eos = [row for row in eos if row["source_id"] == SOURCE_ID]
    cfc = [row for row in reference_waveforms if row["catalogue"] == "CFC/SPH"]
    core = [row for row in reference_waveforms if row["catalogue"] == "CoRe"]
    add("CFC/SPH published row count", len(cfc) == 90, detail=f"expected 90, extracted {len(cfc)}")
    add(
        "CoRe narrative-versus-table row count", len(core) == 28, severity="warning",
        detail=(f"article.tex states 28 waveforms, but tables/CORE_data.tex contains {len(core)} numerical rows; "
                "the export preserves the 27 published rows and does not invent the missing record."),
    )
    add("unique waveform IDs", len({row["id"] for row in waveforms}) == len(waveforms))
    eos_names = {row["eos"].upper() for row in reference_eos}
    waveform_eos = {row["eos"].upper() for row in reference_waveforms}
    add("EOS names resolve to eos.csv", waveform_eos <= eos_names, detail=str(sorted(waveform_eos - eos_names)))
    cfc_eos = {row["eos"] for row in cfc}
    add(
        "CFC/SPH narrative-versus-table EOS count", len(cfc_eos) == 13, severity="warning",
        detail=f"article.tex states 13 EOS, but the waveform table contains {len(cfc_eos)} unique identifiers: {sorted(cfc_eos)}",
    )
    eos_without_properties = sorted(row["eos"] for row in reference_eos if not row["r_1_2_km"])
    add(
        "waveform EOS have published property rows", not eos_without_properties, severity="warning",
        detail=f"No TOV_info.tex property row for: {eos_without_properties}",
    )
    chirp_errors = [abs(row["mchirp_msun"] - chirp_mass(row["m1_msun"], row["m2_msun"])) for row in reference_waveforms]
    add("chirp masses agree within table rounding", max(chirp_errors) <= 0.011, detail=f"maximum absolute difference {max(chirp_errors):.6f} Msun")
    q_errors = [abs(row["q_original"] - row["q"]) for row in reference_waveforms]
    add("mass ratios agree within table rounding", max(q_errors) <= 0.011, detail=f"maximum absolute difference {max(q_errors):.6f}")
    add("all reference dominant frequencies are measured", all(row["f_peak_khz"] for row in reference_waveforms))
    add("CoRe secondary frequencies remain missing", all(not row["f_2_0_khz"] and not row["f_spiral_khz"] for row in core))
    duplicate_keys: dict[tuple[Any, ...], list[str]] = {}
    for row in waveforms:
        key = (row["source_id"], row["catalogue"], row["simulation_id"], row["eos"],
               row["m1_msun"], row["m2_msun"], row["f_peak_khz"])
        duplicate_keys.setdefault(key, []).append(row["id"])
    duplicates = [ids for ids in duplicate_keys.values() if len(ids) > 1]
    add("no exact duplicate waveform rows", not duplicates, detail=json.dumps(duplicates))
    relation_ids = {row["relation_id"] for row in relations}
    add("all coefficients resolve to a relation", all(row["relation_id"] in relation_ids for row in coefficients))
    record_ids = {row["id"] for row in waveforms} | {row["id"] for row in eos} | relation_ids
    provenance_ids = {row["record_id"] for row in provenance}
    add("all public records have provenance", record_ids <= provenance_ids, detail=str(sorted(record_ids - provenance_ids)))
    add("missing frequencies are never encoded as zero", all(row["f_2_0_khz"] != 0 and row["f_spiral_khz"] != 0 for row in waveforms))
    add("every waveform row reports at least one frequency",
        all(any(row.get(field) not in (None, "") for field in FREQUENCY_FIELDS) for row in waveforms))
    errors = [check for check in checks if check["status"] == "error"]
    warnings = [check for check in checks if check["status"] == "warning"]
    return {
        "status": "failed" if errors else ("passed_with_warnings" if warnings else "passed"),
        "summary": {"waveforms": len(waveforms), "cfc_sph": len(cfc), "core": len(core), "eos": len(eos),
                    "relations": len(relations), "coefficients": len(coefficients), "errors": len(errors), "warnings": len(warnings)},
        "checks": checks,
    }


def add_collection_validation(validation: dict[str, Any], sources: list[dict[str, Any]],
                              tables: list[dict[str, Any]], equations: list[dict[str, Any]],
                              dependencies: list[dict[str, Any]]) -> None:
    source_ids = {record["source_id"] for record in sources}
    staged_ids = {record["source_id"] for record in tables + equations + dependencies}
    checks = validation["checks"]
    checks.append({
        "name": "all seed papers are source registered", "status": "pass" if len(sources) == EXPECTED_SOURCE_COUNT else "error",
        "detail": f"expected {EXPECTED_SOURCE_COUNT}, registered {len(sources)}",
    })
    checks.append({
        "name": "all staging records resolve to sources.csv", "status": "pass" if staged_ids <= source_ids else "error",
        "detail": str(sorted(staged_ids - source_ids)),
    })
    checks.append({
        "name": "all registered source projects were scanned", "status": "pass" if all(record["local_source_root"] for record in sources) else "error",
        "detail": str([record["source_id"] for record in sources if not record["local_source_root"]]),
    })
    errors = sum(check["status"] == "error" for check in checks)
    warnings = sum(check["status"] == "warning" for check in checks)
    validation["summary"].update({
        "sources_registered": len(sources), "tables_inventoried": len(tables),
        "equations_inventoried": len(equations), "dependencies_inventoried": len(dependencies),
        "errors": errors, "warnings": warnings,
    })
    validation["status"] = "failed" if errors else ("passed_with_warnings" if warnings else "passed")


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_documentation(data_dir: Path, table_report: dict[str, Any], validation: dict[str, Any],
                        source_count: int, inventory_counts: dict[str, int]) -> None:
    readme = f"""# Community BNS postmerger dataset

This directory is the public, CSV-based extraction of the complete {source_count}-paper seed
corpus. It is generated deterministically by `scripts/extract_reference_data.py`
from the preserved arXiv LaTeX source projects.

- `waveforms.csv`: normalized simulation configurations with at least one reported frequency.
- `eos.csv`: source-specific EOS identifiers and published stellar properties.
- `sources.csv`: publication-level attribution.
- `extraction_coverage.csv`: per-paper structural and scientific-review coverage.
- `provenance.csv`: exact source table, line, and original LaTeX row for every record.
- `relations/relations.csv`: published empirical-relation inventory.
- `relations/coefficients.csv`: normalized coefficient values and terms.
- `measurements_extra.csv`: sparse paper-specific measurements linked to waveform rows.
- `published_tables.csv`: every detected published LaTeX table with source provenance.
- `published_table_cells.csv`: one lossless row per published table cell, including a
  best-effort numeric value while retaining the original LaTeX.
- `published_equations.csv`: every detected equation environment and its local context.
- `staging/equations.jsonl`: labeled and unlabeled equation environments with context.
- `staging/all_equations.jsonl`: equations structurally extracted from every collected paper.
- `staging/table_inventory.csv`: all detected LaTeX tables, classified as review candidates.
- `staging/table_rows.jsonl`: source-linked raw cells from every detected table.
- `staging/dependencies.csv`: `\\input` and `\\include` dependency resolution for every paper.
- `validation_report.json`: automated scientific and structural checks.
- `review_issues.csv`: unresolved interpretations requiring human review.

The normative extraction rules are in
[`docs/extraction_conventions.md`](../docs/extraction_conventions.md); canonical
frequency definitions are in
[`docs/frequency_nomenclature.md`](../docs/frequency_nomenclature.md), and paper-local
symbol mappings are in
[`database/notation/paper_frequency_aliases.csv`](../database/notation/paper_frequency_aliases.csv).

Empty frequency cells are missing values, never zero. Their companion status columns
explain whether the source table omitted or did not identify a feature. The standardized
mass ratio is `q = min(m1,m2)/max(m1,m2) <= 1`; the source value and convention are
retained separately.

Configurations with every frequency field empty are excluded from `waveforms.csv`.
Their original tables remain available in the lossless exports, and papers contributing
only empirical relations remain represented in the relation catalogue.

All {source_count} collected papers are represented in `sources.csv`, `published_tables.csv`, and/or
`published_equations.csv` according to their source contents. Reviewed adapters normalize
compatible simulation and EOS tables into the compact domain CSVs; the lossless public
exports ensure information from papers with incompatible schemas is still queryable.

Regenerate from the repository root with:

```sh
python3 scripts/extract_reference_data.py
```
"""
    (data_dir / "README.md").write_text(readme, encoding="utf-8")
    schema = """# Dataset schema

The field definitions below are governed by
[`docs/extraction_conventions.md`](../docs/extraction_conventions.md). Frequency
semantics are further specified by
[`docs/frequency_nomenclature.md`](../docs/frequency_nomenclature.md) and
[`database/notation/paper_frequency_aliases.csv`](../database/notation/paper_frequency_aliases.csv).

## `waveforms.csv`

Masses are in solar masses, postmerger frequencies in kHz, and initial binary GW
frequencies in Hz. `simulation_id` retains the published identifier when one exists;
it is empty for the 2020 CoRe appendix because that table does not provide the original
identifiers. `spectral_type` remains `unknown` unless a source states it explicitly.

Every row contains at least one reported frequency. Source tables that describe only
simulation configurations, collapse outcomes, or empirical-relation calibration inputs
remain in the lossless exports and do not create frequency-empty waveform rows.

The standardized `q` is always the smaller component mass divided by the larger.
`q_original` and `q_original_definition` preserve the table convention. Missing
secondary features use an empty numeric cell plus `f_2_0_status` or
`f_spiral_status`; no empirical relation is used to fill them.

Frequency columns follow `docs/frequency_nomenclature.md`. In particular,
`f_peak_khz` is a static dominant postmerger spectral maximum, while
`f_peak_early_khz`, `f_peak_late_khz`, `f_peak_mean_khz`,
`f_peak_instantaneous_khz`, and `f_merger_khz` remain distinct. Paper-local
symbol mappings and unresolved cases are recorded in
`database/notation/paper_frequency_aliases.csv`.

## `eos.csv`

Each row is a source-specific EOS record. `r_1_2_km` through `r_1_8_km` are radii
of cold, nonrotating stars at the stated masses. They are not remnant radii. Properties
published at other reference masses are retained in `definition_notes` rather than put
in a mismatched radius column.

## Relations

`relations.csv` stores the equation family, variables, calibration population,
applicability, residual statistics, and evidence location. `coefficients.csv` maps
each `b0`–`b5` (or explicit-equation coefficient) to its mathematical term.
The equations are an inventory for review and are not yet a callable Julia API.

## Corpus-wide lossless exports

`published_tables.csv`, `published_table_cells.csv`, and `published_equations.csv` cover
the complete source corpus. The cell table retains both `value_latex` and a cleaned
`value_text`; `numeric_value` is only a convenience extraction of the central number and
must be interpreted with its table header and source context. `measurements_extra.csv`
stores reviewed quantities that do not have a stable column in `waveforms.csv`.

## Provenance and identifiers

Every paper has a stable `arxiv-<identifier>` key in `sources.csv`; all public and
staging records carry that `source_id`. Record IDs extend the source key with a
catalogue- or record-specific suffix. Every public record resolves to a row in
`provenance.csv`, which preserves the original LaTeX cell row and line range.
"""
    (data_dir / "schema.md").write_text(schema, encoding="utf-8")
    report_lines = [
        "# Corpus extraction report", "",
        f"Sources: {source_count}-paper BNS postmerger seed corpus, with Vretinaris, Stergioulas & Bauswein (2020) as the reference adapter.", "",
        "Governing policies: [`docs/extraction_conventions.md`](../docs/extraction_conventions.md). "
        "Frequency vocabulary: [`docs/frequency_nomenclature.md`](../docs/frequency_nomenclature.md).", "",
        "## Extracted structures", "",
    ]
    for name, info in table_report.items():
        report_lines.append(f"- `{name}`: `{info['source_path']}`; " + ", ".join(f"{key}={value}" for key, value in info.items() if key.endswith("records") or key in {"latex_rows", "waveform_records"}))
    report_lines.extend([
        "", "## Count investigation", "",
        "The CFC/SPH appendix table contains 45 physical LaTeX rows with two waveform entries per row, yielding the stated 90 records.",
        "The manuscript narrative states that 28 CoRe waveforms were used, but `tables/CORE_data.tex` contains only 27 numerical rows. No omitted row can be reconstructed from the published table, so `waveforms.csv` contains 27 CoRe records and `review_issues.csv` records the discrepancy.",
        "The CFC/SPH text states 13 EOS while the frequency table contains 12 unique identifiers. SHEN and SLY4 have no row in `TOV_info.tex`; they remain distinct EOS registry entries with missing properties rather than being aliased or filled.",
        "", "## Interpretation policy", "",
        "Dashes in CFC/SPH secondary-frequency cells are retained as missing with status `not_reported_or_not_identified`. CoRe secondary frequencies are missing with status `not_reported_for_catalogue`, because the manuscript explicitly says only the dominant frequency was extracted for that subset. Spectral classes are not inferred from peak presence.",
        "", f"Validation status: **{validation['status']}**.", "",
        "## Collection-wide structural coverage", "",
        f"The source registry contains {source_count} papers. The generic pass found "
        f"{inventory_counts['tables']} tables, {inventory_counts['table_rows']} table rows, "
        f"{inventory_counts['equations']} equations, and {inventory_counts['dependencies']} input/include dependencies. "
        "Every detected table cell and equation is published with source IDs and line numbers. Reviewed paper adapters additionally normalize compatible waveform and EOS records; other records retain their original text rather than receiving guessed semantics.", "",
    ])
    (data_dir / "extraction_report.md").write_text("\n".join(report_lines), encoding="utf-8")


def extract(source: Path, data_dir: Path, papers_dir: Path = Path("papers")) -> dict[str, Any]:
    required = [
        "article.tex", "tables/bauswein_data.tex", "tables/CORE_data.tex", "tables/TOV_info.tex",
        "tables/tables_combined_fRM.tex", "tables/tables_combined.tex",
    ]
    missing = [relative for relative in required if not (source / relative).is_file()]
    if missing:
        raise FileNotFoundError("missing reference sources: " + ", ".join(missing))

    waveforms, waveform_provenance, waveform_report = extract_waveforms(source)
    eos, eos_provenance, eos_report = extract_eos(source)
    complete_eos_registry(waveforms, eos, eos_provenance, waveform_provenance)
    frequency_relations, frequency_coefficients, frequency_provenance = extract_relation_table(
        source, "tables/tables_combined_fRM.tex", "frequency_from_radius"
    )
    radius_relations, radius_coefficients, radius_provenance = extract_relation_table(
        source, "tables/tables_combined.tex", "radius_from_frequency"
    )
    equations = extract_equations(source)
    tidal_relation, tidal_coefficients, tidal_provenance = explicit_relation(equations)
    relations = frequency_relations + radius_relations + [tidal_relation]
    coefficients = frequency_coefficients + radius_coefficients + tidal_coefficients
    provenance = waveform_provenance + eos_provenance + frequency_provenance + radius_provenance + [tidal_provenance]

    sources = load_source_registry(papers_dir)
    if SOURCE_ID not in {record["source_id"] for record in sources}:
        raise ValueError(f"reference source {SOURCE_ID} is absent from {papers_dir}")
    all_tables, all_table_rows, all_equations, all_dependencies = scan_all_sources(sources)
    additional_waveforms, additional_eos, measurements_extra, additional_provenance = extract_additional_papers(
        all_tables, all_table_rows
    )
    additional_relations, additional_coefficients, additional_relation_provenance = extract_additional_relations(
        all_tables, all_table_rows, all_equations
    )
    waveforms.extend(additional_waveforms)
    eos.extend(additional_eos)
    relations.extend(additional_relations)
    coefficients.extend(additional_coefficients)
    provenance.extend(additional_provenance + additional_relation_provenance)
    waveforms, measurements_extra, provenance = retain_frequency_records(
        waveforms, measurements_extra, provenance
    )
    complete_collection_eos_registry(waveforms, eos, provenance)
    published_cells, published_equations = publication_exports(all_tables, all_table_rows, all_equations)
    validation = validate(waveforms, eos, relations, coefficients, provenance)
    coverage = extraction_coverage(
        sources, all_tables, all_table_rows, all_equations, all_dependencies,
        waveforms, eos, relations,
    )
    add_collection_validation(validation, sources, all_tables, all_equations, all_dependencies)
    review_issues = [{
        "issue_id": "vretinaris2020-core-count-001", "severity": "warning",
        "record_type": "catalogue", "record_id": "vretinaris2020-core",
        "source_path": "article.tex; tables/CORE_data.tex",
        "issue": "Narrative states 28 CoRe waveforms but the published table contains 27 numerical rows.",
        "resolution": "Export all 27 published rows; do not synthesize the absent record; seek author/source clarification.",
        "status": "open",
    }, {
        "issue_id": "vretinaris2020-cfcsph-eos-count-001", "severity": "warning",
        "record_type": "catalogue", "record_id": "vretinaris2020-cfcsph",
        "source_path": "article.tex; tables/bauswein_data.tex",
        "issue": "Narrative states 13 CFC/SPH EOS, but the published frequency table contains 12 unique EOS identifiers.",
        "resolution": "Preserve all 12 table identifiers; do not infer an omitted EOS; seek author/source clarification.",
        "status": "open",
    }, {
        "issue_id": "vretinaris2020-eos-properties-001", "severity": "warning",
        "record_type": "eos", "record_id": "arxiv-1910-10856-eos-registry",
        "source_path": "tables/bauswein_data.tex; tables/TOV_info.tex",
        "issue": "SHEN and SLY4 occur in the waveform table but not in the source EOS-property table.",
        "resolution": "Create source-linked EOS registry rows with empty properties; do not alias SLY4 to SLy or invent radii.",
        "status": "open",
    }]

    write_csv(data_dir / "waveforms.csv", WAVEFORM_FIELDS, waveforms)
    write_csv(data_dir / "eos.csv", EOS_FIELDS, eos)
    write_csv(data_dir / "sources.csv", SOURCE_FIELDS, sources)
    write_csv(data_dir / "extraction_coverage.csv", COVERAGE_FIELDS, coverage)
    write_csv(data_dir / "provenance.csv", PROVENANCE_FIELDS, provenance)
    write_csv(data_dir / "relations/relations.csv", RELATION_FIELDS, relations)
    write_csv(data_dir / "relations/coefficients.csv", COEFFICIENT_FIELDS, coefficients)
    write_csv(data_dir / "measurements_extra.csv", MEASUREMENT_EXTRA_FIELDS, measurements_extra)
    write_csv(data_dir / "published_tables.csv", PUBLISHED_TABLE_FIELDS, all_tables)
    write_csv(data_dir / "published_table_cells.csv", PUBLISHED_CELL_FIELDS, published_cells)
    write_csv(data_dir / "published_equations.csv", PUBLISHED_EQUATION_FIELDS, published_equations)
    write_csv(data_dir / "review_issues.csv", list(review_issues[0]), review_issues)
    write_jsonl(data_dir / "staging/equations.jsonl", equations)
    write_jsonl(data_dir / "staging/waveforms.jsonl", waveforms)
    write_csv(data_dir / "staging/table_inventory.csv", TABLE_INVENTORY_FIELDS, all_tables)
    write_jsonl(data_dir / "staging/table_rows.jsonl", all_table_rows)
    write_jsonl(data_dir / "staging/all_equations.jsonl", all_equations)
    write_csv(data_dir / "staging/dependencies.csv", DEPENDENCY_FIELDS, all_dependencies)
    write_json(data_dir / "validation_report.json", validation)
    table_report = {**waveform_report, "EOS": eos_report,
                    "frequency_relations": {"source_path": "tables/tables_combined_fRM.tex", "relation_records": len(frequency_relations)},
                    "radius_relations": {"source_path": "tables/tables_combined.tex", "relation_records": len(radius_relations)}}
    inventory_counts = {"tables": len(all_tables), "table_rows": len(all_table_rows),
                        "equations": len(all_equations), "dependencies": len(all_dependencies)}
    write_documentation(data_dir, table_report, validation, len(sources), inventory_counts)
    checksums = {}
    for path in sorted(item for item in data_dir.rglob("*") if item.is_file() and item.name != "checksums.json"):
        checksums[path.relative_to(data_dir).as_posix()] = file_sha256(path)
    write_json(data_dir / "checksums.json", checksums)
    return validation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--papers-dir", type=Path, default=Path("papers"))
    args = parser.parse_args(argv)
    validation = extract(args.source, args.data_dir, args.papers_dir)
    print(json.dumps(validation["summary"], indent=2))
    print(f"Validation: {validation['status']}")
    return 1 if validation["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
