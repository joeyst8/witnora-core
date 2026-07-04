"""Official CNFgen XOR diagnostic runner for Witnora-Core v0.9.4.

This module is a benchmark/reporting harness only. It does not add solver
logic or broaden XOR detection.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any
import zipfile

from .benchmark import structural_metrics
from .certificate import XOR_UNSAT_NATIVE
from .cnf import CNFFormula
from .cnfgen_matrix import cnfgen_version
from .dimacs import parse_dimacs
from .proof import export_certificate_bundle
from .public_benchmarks import (
    ERROR,
    NO_COLLAPSE_FOUND,
    PUBLIC_CATEGORIES,
    SAT_ASSIGNMENT_VERIFIED,
    UNSAT_DRAT_EXPORTED_VERIFIED,
    UNSAT_NOT_EXTERNALLY_VERIFIED,
    UNSUPPORTED_DRAT,
    UNSAT_XOR_NATIVE_ONLY,
    find_cnfgen_cli,
)
from .runner import solve_with_xor
from .xor import XOR_PATTERN_SKIPPED_MAX_K, detect_cnf_xor_patterns

DIAGNOSTIC_VERSION = "0.9.4"
DEFAULT_C_VALUES = [2, 3, 4]
BASELINE_MAX_K = 6
SENSITIVITY_MAX_K_VALUES = [4, 5, 6]
DEFAULT_TIMEOUT_SECONDS = 300.0
DEFAULT_XOR_DRAT_MAX_DETECTED_EQUATIONS = 6
DEFAULT_XOR_DRAT_MAX_SOURCE_CLAUSES = 48
XOR_DRAT_SKIPPED_DIAGNOSTIC_CAP = "XOR_DRAT_SKIPPED_DIAGNOSTIC_CAP"


BASELINE_V084_ROWS: list[dict[str, Any]] = [
    {
        "family": "pigeonhole",
        "c": c,
        "total": 8,
        "SAT_ASSIGNMENT_VERIFIED": 0,
        "UNSAT_DRAT_EXPORTED_VERIFIED": 1,
        "NO_COLLAPSE_FOUND": 7,
    }
    for c in DEFAULT_C_VALUES
] + [
    {
        "family": "tseitin",
        "c": c,
        "total": 4,
        "SAT_ASSIGNMENT_VERIFIED": 0,
        "UNSAT_DRAT_EXPORTED_VERIFIED": 0,
        "NO_COLLAPSE_FOUND": 4,
    }
    for c in DEFAULT_C_VALUES
] + [
    {
        "family": "parity",
        "c": c,
        "total": 3,
        "SAT_ASSIGNMENT_VERIFIED": 0,
        "UNSAT_DRAT_EXPORTED_VERIFIED": 0,
        "NO_COLLAPSE_FOUND": 3,
    }
    for c in DEFAULT_C_VALUES
]


def stable_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def sha256_file(path: str | Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def git_metadata() -> dict[str, str]:
    def run_git(args: list[str]) -> str:
        try:
            proc = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
        except OSError:
            return ""
        if proc.returncode != 0:
            return ""
        return proc.stdout.strip()

    return {
        "commit": run_git(["rev-parse", "HEAD"]),
        "tag": run_git(["describe", "--tags", "--exact-match"]),
    }


def cnfgen_specs(family: str) -> list[tuple[str, list[str]]]:
    if family == "pigeonhole":
        return [
            (f"php_{pigeons}_{pigeons - 1}", ["php", str(pigeons), str(pigeons - 1)])
            for pigeons in range(3, 11)
        ]
    if family == "tseitin":
        return [
            (f"tseitin_{n}", ["--seed", str(n), "tseitin", str(n)])
            for n in [10, 15, 20, 30]
        ]
    if family == "parity":
        return [(f"parity_{n}", ["parity", str(n)]) for n in [12, 16, 20]]
    raise ValueError(f"unsupported family: {family}")


def run_cnfgen_command(cnfgen: str, args: list[str], output_path: Path) -> dict[str, Any]:
    command = [cnfgen, *args]
    started = time.perf_counter()
    proc = subprocess.run(command, capture_output=True, text=True, check=False)
    elapsed = round(time.perf_counter() - started, 6)
    result = {
        "command": " ".join(command),
        "exit_code": proc.returncode,
        "stdout_excerpt": proc.stdout[:1000],
        "stderr_excerpt": proc.stderr[:1000],
        "runtime_seconds": elapsed,
        "output_path": str(output_path),
    }
    if proc.returncode == 0 and proc.stdout.strip():
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(proc.stdout, encoding="utf-8")
        result["generated"] = True
    else:
        result["generated"] = False
    return result


def generate_official_cases(root: Path, cnfgen: str, families: list[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    generation: dict[str, Any] = {"families": {}, "commands": []}
    for family in families:
        generation["families"][family] = {"instances": [], "failures": []}
        for instance_id, args in cnfgen_specs(family):
            output_path = root / "generated_dimacs" / family / f"{instance_id}.cnf"
            command_result = run_cnfgen_command(cnfgen, args, output_path)
            generation["commands"].append(command_result["command"])
            if not command_result["generated"]:
                generation["families"][family]["failures"].append(
                    {"instance_id": instance_id, **command_result}
                )
                continue
            case = {
                "instance_id": instance_id,
                "family": family,
                "dimacs_path": str(output_path),
                "generation_command": command_result["command"],
            }
            cases.append(case)
            generation["families"][family]["instances"].append(case)
    return cases, generation


def _read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _category_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {category: 0 for category in PUBLIC_CATEGORIES}
    for row in rows:
        category = str(row.get("public_category", ERROR))
        counts[category] = counts.get(category, 0) + 1
    return counts


def _count_skipped_over_max_k(diagnostics: list[dict[str, Any]]) -> int:
    return sum(1 for item in diagnostics if item.get("reason") == XOR_PATTERN_SKIPPED_MAX_K)


def run_instance(
    case: dict[str, Any],
    *,
    c: int,
    max_k: int,
    group: str,
    output_root: Path,
    drat_trim_path: str | None,
    timeout_seconds: float,
    xor_drat_max_detected_equations: int,
    xor_drat_max_source_clauses: int,
) -> dict[str, Any]:
    started = time.perf_counter()
    instance_id = str(case["instance_id"])
    family = str(case["family"])
    dimacs_path = Path(str(case["dimacs_path"]))
    row: dict[str, Any] = {
        "group": group,
        "instance_id": instance_id,
        "family": family,
        "c": c,
        "max_k": max_k,
        "dimacs_path": str(dimacs_path),
        "generation_command": case.get("generation_command", ""),
        "timeout_seconds": timeout_seconds,
        "error_message": "",
        "proof_base": "",
        "proof_drat_path": "",
        "drat_export_status": "",
        "external_checker": "",
        "external_checker_ran": False,
        "external_checker_verified": False,
        "external_drat": False,
        "drat_claim": "NOT_EXPORTED",
        "xor_status": "",
        "xor_drat_status": "",
        "xor_drat_skip_reason": "",
        "xor_drat_verified": False,
        "solver_time_seconds": 0.0,
        "drat_export_time_seconds": 0.0,
        "drat_trim_time_seconds": 0.0,
        "collapse_path_length": 0,
    }
    try:
        formula = parse_dimacs(dimacs_path.read_text(encoding="utf-8"))
        metrics = structural_metrics(formula)
        detected = detect_cnf_xor_patterns(formula, max_k=max_k)
        row.update(
            {
                "num_vars": formula.num_vars,
                "num_clauses": formula.num_clauses,
                "original_num_vars": metrics["num_vars"],
                "original_num_clauses": metrics["num_clauses"],
                "original_max_clause_width": metrics["max_clause_width"],
                "detected_xor_equations": len(detected.equations),
                "max_detected_arity": max((len(eq.variables) for eq in detected.equations), default=0),
                "skipped_over_max_k": _count_skipped_over_max_k(list(detected.diagnostics)),
                "xor_source_clause_count": sum(len(eq.source_clauses) for eq in detected.equations),
            }
        )
        solve_started = time.perf_counter()
        path = solve_with_xor(
            formula,
            c=c,
            detect_cnf_xor=True,
            detect_xor_max_k=max_k,
        )
        solver_seconds = round(time.perf_counter() - solve_started, 6)
        detected_source_clauses = int(row.get("xor_source_clause_count", 0))
        export_xor_drat = True
        xor_drat_skip_reason = ""
        if path.status == XOR_UNSAT_NATIVE and (
            len(detected.equations) > xor_drat_max_detected_equations
            or detected_source_clauses > xor_drat_max_source_clauses
        ):
            export_xor_drat = False
            xor_drat_skip_reason = XOR_DRAT_SKIPPED_DIAGNOSTIC_CAP
            row["xor_drat_skip_reason"] = xor_drat_skip_reason
        cert_dir = output_root / "certs" / group / family / f"c{c}" / f"k{max_k}" / f"{instance_id}.wcert"
        export_started = time.perf_counter()
        export_certificate_bundle(
            formula,
            path,
            cert_dir,
            original_dimacs_text=dimacs_path.read_text(encoding="utf-8"),
            export_drat=True,
            export_xor_drat=export_xor_drat,
            drat_trim_path=drat_trim_path,
        )
        export_seconds = round(time.perf_counter() - export_started, 6)
        result_json = _read_json_if_exists(cert_dir / "result.json")
        drat_status = _read_json_if_exists(cert_dir / "drat_status.json")
        xor_status = _read_json_if_exists(cert_dir / "xor_status.json")
        xor_drat_status = _read_json_if_exists(cert_dir / "xor_drat_status.json")
        public_category = str(result_json.get("public_category", path.public_category))
        external_verified = bool(drat_status.get("external_checker_verified", False))
        if (
            result_json.get("logical_status", path.logical_status) == "UNSAT"
            and drat_status.get("drat_export_status") == "EXPORTED"
            and drat_status.get("proof_scope") == "END_TO_END_FROM_ORIGINAL_CNF"
            and drat_status.get("checked_against") == "original.dimacs"
            and external_verified
        ):
            public_category = UNSAT_DRAT_EXPORTED_VERIFIED
        certification_level = (
            "EXTERNAL_DRAT_VERIFIED"
            if public_category == UNSAT_DRAT_EXPORTED_VERIFIED
            else result_json.get("certification_level", path.public_certification_level)
        )
        proof_base = (
            "original_cnf"
            if public_category == UNSAT_DRAT_EXPORTED_VERIFIED
            else result_json.get("proof_base")
        )
        proof_path = cert_dir / "proof.drat"
        row.update(
            {
                "status": result_json.get("logical_status", path.logical_status),
                "internal_status": result_json.get("status", path.status),
                "final_class": result_json.get("final_class", path.final_class),
                "discovery_route": result_json.get("discovery_route", path.discovery_route),
                "certification_level": certification_level,
                "public_category": public_category,
                "certificate_hash": result_json.get("certificate_hash", path.certificate_hash),
                "wcert_path": str(cert_dir),
                "proof_drat_path": str(proof_path) if proof_path.exists() else "",
                "drat_export_status": drat_status.get("drat_export_status", ""),
                "external_checker": drat_status.get("external_checker", ""),
                "external_checker_ran": bool(drat_status.get("external_checker_ran", False)),
                "external_checker_verified": external_verified,
                "external_drat": bool(result_json.get("external_drat", False)) or public_category == UNSAT_DRAT_EXPORTED_VERIFIED,
                "drat_claim": "EXPORTED_VERIFIED"
                if public_category == UNSAT_DRAT_EXPORTED_VERIFIED
                else result_json.get("drat_claim", "NOT_EXPORTED"),
                "proof_base": proof_base,
                "xor_status": xor_status.get("xor_status", ""),
                "xor_drat_status": xor_drat_status.get("xor_drat_status", xor_drat_skip_reason),
                "xor_drat_verified": bool(xor_drat_status.get("external_drat", False)),
                "strict_unsat_external_pass": public_category
                not in {UNSAT_XOR_NATIVE_ONLY, UNSAT_NOT_EXTERNALLY_VERIFIED, UNSUPPORTED_DRAT},
                "solver_time_seconds": solver_seconds,
                "drat_export_time_seconds": export_seconds,
                "drat_trim_time_seconds": float(drat_status.get("drat_trim_time_seconds", 0.0) or 0.0),
                "collapse_path_length": len(path.steps),
                "total_time_seconds": round(time.perf_counter() - started, 6),
            }
        )
    except Exception as exc:  # pragma: no cover - diagnostic isolation
        row.update(
            {
                "status": ERROR,
                "internal_status": ERROR,
                "public_category": ERROR,
                "strict_unsat_external_pass": False,
                "error_message": str(exc),
                "total_time_seconds": round(time.perf_counter() - started, 6),
            }
        )
    return row


def baseline_summary_payload() -> dict[str, Any]:
    return {
        "source": "v0.8.4 official CNFgen diagnostic artifact summary supplied for v0.9.4 comparison",
        "rows": BASELINE_V084_ROWS,
        "note": "Instance IDs are regenerated with the same official CNFgen command families/sizes when local v0.8.4 artifact manifests are unavailable.",
    }


def summarize_rows(rows: list[dict[str, Any]], *, group: str | None = None) -> list[dict[str, Any]]:
    selected = [row for row in rows if group is None or row.get("group") == group]
    summaries: list[dict[str, Any]] = []
    for family in sorted({str(row.get("family", "")) for row in selected}):
        for c in sorted({int(row.get("c", 0)) for row in selected if row.get("family") == family}):
            family_rows = [row for row in selected if row.get("family") == family and int(row.get("c", 0)) == c]
            counts = _category_counts(family_rows)
            solved = [
                row
                for row in family_rows
                if row.get("public_category") in {SAT_ASSIGNMENT_VERIFIED, UNSAT_DRAT_EXPORTED_VERIFIED}
            ]
            no_collapse = [row for row in family_rows if row.get("public_category") == NO_COLLAPSE_FOUND]
            summaries.append(
                {
                    "group": group or "all",
                    "family": family,
                    "c": c,
                    "total_cases": len(family_rows),
                    **counts,
                    "strict_unsat_external_pass": all(row.get("strict_unsat_external_pass", False) for row in family_rows),
                    "externally_verified_unsat_count": counts.get(UNSAT_DRAT_EXPORTED_VERIFIED, 0),
                    "max_instance_solved": str(solved[-1].get("instance_id", "")) if solved else "",
                    "first_no_collapse_instance": str(no_collapse[0].get("instance_id", "")) if no_collapse else "",
                    "average_solver_time_seconds": _average(row.get("solver_time_seconds") for row in family_rows),
                    "average_drat_trim_time_seconds": _average(row.get("drat_trim_time_seconds") for row in family_rows),
                    "average_collapse_path_length": _average(row.get("collapse_path_length") for row in family_rows),
                }
            )
    return summaries


def _average(values: list[Any] | Any) -> float:
    parsed = []
    for value in values:
        if value not in (None, ""):
            try:
                parsed.append(float(value))
            except (TypeError, ValueError):
                pass
    return round(sum(parsed) / len(parsed), 6) if parsed else 0.0


def compare_baseline_v094(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    baseline_lookup = {(row["family"], int(row["c"])): row for row in BASELINE_V084_ROWS}
    v094_summaries = summarize_rows([row for row in rows if row.get("group") == "baseline_compat"], group="baseline_compat")
    comparison: list[dict[str, Any]] = []
    for row in v094_summaries:
        baseline = baseline_lookup.get((row["family"], int(row["c"])), {})
        baseline_solved = int(baseline.get("SAT_ASSIGNMENT_VERIFIED", 0)) + int(
            baseline.get("UNSAT_DRAT_EXPORTED_VERIFIED", 0)
        )
        v094_solved = int(row.get(SAT_ASSIGNMENT_VERIFIED, 0)) + int(row.get(UNSAT_DRAT_EXPORTED_VERIFIED, 0))
        comparison.append(
            {
                "family": row["family"],
                "c": row["c"],
                "baseline_total": baseline.get("total", 0),
                "baseline_SAT_ASSIGNMENT_VERIFIED": baseline.get("SAT_ASSIGNMENT_VERIFIED", 0),
                "baseline_UNSAT_DRAT_EXPORTED_VERIFIED": baseline.get("UNSAT_DRAT_EXPORTED_VERIFIED", 0),
                "baseline_NO_COLLAPSE_FOUND": baseline.get("NO_COLLAPSE_FOUND", 0),
                "v094_total": row.get("total_cases", 0),
                "v094_SAT_ASSIGNMENT_VERIFIED": row.get(SAT_ASSIGNMENT_VERIFIED, 0),
                "v094_UNSAT_DRAT_EXPORTED_VERIFIED": row.get(UNSAT_DRAT_EXPORTED_VERIFIED, 0),
                "v094_UNSAT_XOR_NATIVE_ONLY": row.get(UNSAT_XOR_NATIVE_ONLY, 0),
                "v094_NO_COLLAPSE_FOUND": row.get(NO_COLLAPSE_FOUND, 0),
                "delta_solved_externally_verified": v094_solved - baseline_solved,
            }
        )
    return comparison


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def report_markdown(comparison: list[dict[str, Any]], rows: list[dict[str, Any]], failures: list[dict[str, Any]]) -> str:
    lines = [
        "# Witnora-Core v0.9.4 Official CNFgen XOR Diagnostic",
        "",
        "This is a diagnostic benchmark, not a competitive SAT benchmark.",
        "Every UNSAT counted as DRAT verified must have real `drat-trim` verification.",
        "",
        "## Executive Summary",
        "",
    ]
    counts = _category_counts(rows)
    lines.extend(
        [
            f"- Total diagnostic rows: {len(rows)}",
            f"- SAT_ASSIGNMENT_VERIFIED: {counts.get(SAT_ASSIGNMENT_VERIFIED, 0)}",
            f"- UNSAT_DRAT_EXPORTED_VERIFIED: {counts.get(UNSAT_DRAT_EXPORTED_VERIFIED, 0)}",
            f"- UNSAT_XOR_NATIVE_ONLY: {counts.get(UNSAT_XOR_NATIVE_ONLY, 0)}",
            f"- NO_COLLAPSE_FOUND: {counts.get(NO_COLLAPSE_FOUND, 0)}",
            f"- ERROR: {counts.get(ERROR, 0)}",
            "",
            "## Baseline vs v0.9.4",
            "",
            "| family | c | baseline_total | baseline_SAT_ASSIGNMENT_VERIFIED | baseline_UNSAT_DRAT_EXPORTED_VERIFIED | baseline_NO_COLLAPSE_FOUND | v094_total | v094_SAT_ASSIGNMENT_VERIFIED | v094_UNSAT_DRAT_EXPORTED_VERIFIED | v094_UNSAT_XOR_NATIVE_ONLY | v094_NO_COLLAPSE_FOUND | delta_solved_externally_verified |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in comparison:
        lines.append(
            "| {family} | {c} | {baseline_total} | {baseline_SAT_ASSIGNMENT_VERIFIED} | "
            "{baseline_UNSAT_DRAT_EXPORTED_VERIFIED} | {baseline_NO_COLLAPSE_FOUND} | {v094_total} | "
            "{v094_SAT_ASSIGNMENT_VERIFIED} | {v094_UNSAT_DRAT_EXPORTED_VERIFIED} | "
            "{v094_UNSAT_XOR_NATIVE_ONLY} | {v094_NO_COLLAPSE_FOUND} | {delta_solved_externally_verified} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## XOR Detection",
            "",
            "| instance_id | family | c | max_k | detected_xor_equations | max_detected_arity | skipped_over_max_k | xor_drat_skip_reason | xor_drat_verified | public_category |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| {instance_id} | {family} | {c} | {max_k} | {detected_xor_equations} | "
            "{max_detected_arity} | {skipped_over_max_k} | {xor_drat_skip_reason} | "
            "{xor_drat_verified} | {public_category} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## DRAT Verification",
            "",
            "| instance_id | proof_base | proof_file | drat_trim_status | public_category |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| {instance_id} | {proof_base} | {proof_drat_path} | {external_checker_verified} | {public_category} |".format(
                **row
            )
        )
    lines.extend(["", "## Failures / Skips", ""])
    if not failures:
        lines.append("No generation failures or runtime errors were recorded.")
    else:
        lines.append("| instance_id | reason | notes |")
        lines.append("| --- | --- | --- |")
        for item in failures:
            lines.append(f"| {item.get('instance_id', '')} | {item.get('reason', '')} | {item.get('notes', '')} |")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "Allowed claims: this artifact reports exact public categories for the listed official CNFgen instances, and any `UNSAT_DRAT_EXPORTED_VERIFIED` row is backed by real `drat-trim` verification.",
            "",
            "Forbidden claims: no broad SAT performance claim, no competitiveness claim, no full XOR extraction claim, no CryptoMiniSat-style claim, no P vs NP claim, and no large parity/Tseitin claim beyond these exact rows.",
            "",
        ]
    )
    return "\n".join(lines)


def make_artifact_zip(root: Path, zip_path: Path) -> str:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                archive.write(path, path.as_posix())
    return sha256_file(zip_path)


def run_diagnostic(
    out_root: Path,
    *,
    cnfgen_path: str | None,
    drat_trim_path: str | None,
    timeout_seconds: float,
    c_values: list[int],
    sensitivity_max_k: list[int],
    xor_drat_max_detected_equations: int,
    xor_drat_max_source_clauses: int,
) -> dict[str, Any]:
    cnfgen = find_cnfgen_cli(cnfgen_path)
    if cnfgen is None:
        raise RuntimeError("official cnfgen not found")
    out_root.mkdir(parents=True, exist_ok=True)
    cases, generation = generate_official_cases(out_root, cnfgen, ["pigeonhole", "tseitin", "parity"])
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    baseline_cases = [case for case in cases if case["family"] in {"pigeonhole", "tseitin", "parity"}]
    for c in c_values:
        for case in baseline_cases:
            rows.append(
                run_instance(
                    case,
                    c=c,
                    max_k=BASELINE_MAX_K,
                    group="baseline_compat",
                    output_root=out_root,
                    drat_trim_path=drat_trim_path,
                    timeout_seconds=timeout_seconds,
                    xor_drat_max_detected_equations=xor_drat_max_detected_equations,
                    xor_drat_max_source_clauses=xor_drat_max_source_clauses,
                )
            )
    targeted_cases = [case for case in cases if case["family"] in {"tseitin", "parity"}]
    for c in c_values:
        for case in targeted_cases:
            rows.append(
                run_instance(
                    case,
                    c=c,
                    max_k=BASELINE_MAX_K,
                    group="xor_targeted_small",
                    output_root=out_root,
                    drat_trim_path=drat_trim_path,
                    timeout_seconds=timeout_seconds,
                    xor_drat_max_detected_equations=xor_drat_max_detected_equations,
                    xor_drat_max_source_clauses=xor_drat_max_source_clauses,
                )
            )
    for max_k in sensitivity_max_k:
        for c in c_values:
            for case in targeted_cases:
                rows.append(
                    run_instance(
                        case,
                        c=c,
                        max_k=max_k,
                        group="max_k_sensitivity",
                        output_root=out_root,
                        drat_trim_path=drat_trim_path,
                        timeout_seconds=timeout_seconds,
                        xor_drat_max_detected_equations=xor_drat_max_detected_equations,
                        xor_drat_max_source_clauses=xor_drat_max_source_clauses,
                    )
                )
    for row in rows:
        if row.get("public_category") == ERROR or row.get("error_message"):
            failures.append(
                {
                    "instance_id": row.get("instance_id", ""),
                    "reason": row.get("public_category", ERROR),
                    "notes": row.get("error_message", ""),
                }
            )
    comparison = compare_baseline_v094(rows)
    family_summary: list[dict[str, Any]] = []
    for summary_group in sorted({str(row.get("group", "")) for row in rows}):
        family_summary.extend(summarize_rows(rows, group=summary_group))
    category_summary = _category_counts(rows)
    xor_detection_summary = [
        {
            "instance_id": row.get("instance_id"),
            "family": row.get("family"),
            "group": row.get("group"),
            "c": row.get("c"),
            "max_k": row.get("max_k"),
            "detected_xor_equations": row.get("detected_xor_equations"),
            "max_detected_arity": row.get("max_detected_arity"),
            "skipped_over_max_k": row.get("skipped_over_max_k"),
            "xor_source_clause_count": row.get("xor_source_clause_count"),
            "xor_drat_skip_reason": row.get("xor_drat_skip_reason"),
            "public_category": row.get("public_category"),
        }
        for row in rows
    ]
    drat_summary = {
        "drat_trim_path": drat_trim_path or "",
        "externally_verified_count": sum(1 for row in rows if row.get("external_checker_verified") is True),
        "unverified_unsat_count": sum(1 for row in rows if row.get("public_category") == UNSAT_NOT_EXTERNALLY_VERIFIED),
        "xor_native_only_count": sum(1 for row in rows if row.get("public_category") == UNSAT_XOR_NATIVE_ONLY),
        "xor_drat_skipped_diagnostic_cap_count": sum(
            1 for row in rows if row.get("xor_drat_skip_reason") == XOR_DRAT_SKIPPED_DIAGNOSTIC_CAP
        ),
        "false_drat_claims": sum(
            1
            for row in rows
            if row.get("public_category") == UNSAT_DRAT_EXPORTED_VERIFIED
            and row.get("external_checker_verified") is not True
        ),
    }
    git = git_metadata()
    manifest = {
        "diagnostic_version": DIAGNOSTIC_VERSION,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "witnora_tag": git.get("tag") or "uncommitted",
        "witnora_commit": git.get("commit") or "",
        "witnora_baseline_code_tag": "v0.9.3.1",
        "witnora_baseline_code_commit": "9baff30220a8694d6852e9d31f30145cb63bf060",
        "cnfgen_path": cnfgen,
        "cnfgen_version": cnfgen_version(cnfgen),
        "drat_trim_path": drat_trim_path or "",
        "c_values": c_values,
        "baseline_max_k": BASELINE_MAX_K,
        "sensitivity_max_k": sensitivity_max_k,
        "timeout_seconds": timeout_seconds,
        "xor_drat_max_detected_equations": xor_drat_max_detected_equations,
        "xor_drat_max_source_clauses": xor_drat_max_source_clauses,
        "generation": generation,
    }
    environment = {
        "python": sys.version.replace("\n", " "),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cnfgen_path": cnfgen,
        "cnfgen_version": cnfgen_version(cnfgen),
        "drat_trim_path": drat_trim_path or "",
        "witnora_tag": git.get("tag") or "uncommitted",
        "witnora_commit": git.get("commit") or "",
    }
    files: dict[str, Any] = {
        "manifest.json": manifest,
        "environment.json": environment,
        "baseline_v084_summary.json": baseline_summary_payload(),
        "v094_results.json": {"rows": rows},
        "comparison_v084_vs_v094.json": {"rows": comparison},
        "drat_verification_summary.json": drat_summary,
        "failures_or_skips.json": {"items": failures},
    }
    for name, payload in files.items():
        (out_root / name).write_text(stable_json(payload), encoding="utf-8")
    write_csv(
        out_root / "per_instance_results.csv",
        rows,
        [
            "group",
            "instance_id",
            "family",
            "c",
            "max_k",
            "num_vars",
            "num_clauses",
            "detected_xor_equations",
            "max_detected_arity",
            "skipped_over_max_k",
            "xor_source_clause_count",
            "status",
            "internal_status",
            "discovery_route",
            "certification_level",
            "public_category",
            "proof_base",
            "proof_drat_path",
            "drat_export_status",
            "external_checker",
            "external_checker_ran",
            "external_checker_verified",
            "xor_drat_status",
            "xor_drat_skip_reason",
            "solver_time_seconds",
            "drat_export_time_seconds",
            "total_time_seconds",
            "error_message",
        ],
    )
    write_csv(
        out_root / "per_family_summary.csv",
        family_summary,
        [
            "group",
            "family",
            "c",
            "total_cases",
            *PUBLIC_CATEGORIES,
            "strict_unsat_external_pass",
            "externally_verified_unsat_count",
            "max_instance_solved",
            "first_no_collapse_instance",
            "average_solver_time_seconds",
        ],
    )
    write_csv(
        out_root / "public_category_summary.csv",
        [{"public_category": category, "count": count} for category, count in category_summary.items()],
        ["public_category", "count"],
    )
    write_csv(
        out_root / "xor_detection_summary.csv",
        xor_detection_summary,
        [
            "instance_id",
            "family",
            "group",
            "c",
            "max_k",
            "detected_xor_equations",
            "max_detected_arity",
            "skipped_over_max_k",
            "xor_source_clause_count",
            "xor_drat_skip_reason",
            "public_category",
        ],
    )
    (out_root / "OFFICIAL_XOR_DIAGNOSTIC_REPORT.md").write_text(
        report_markdown(comparison, rows, failures),
        encoding="utf-8",
    )
    return {
        "manifest": manifest,
        "rows": rows,
        "comparison": comparison,
        "family_summary": family_summary,
        "category_summary": category_summary,
        "xor_detection_summary": xor_detection_summary,
        "drat_summary": drat_summary,
        "failures": failures,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run official CNFgen XOR diagnostic")
    parser.add_argument("--out-root", default="outputs/v0.9.4-official-xor-diagnostic")
    parser.add_argument("--cnfgen-path")
    parser.add_argument("--drat-trim")
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--c-values", nargs="+", type=int, default=DEFAULT_C_VALUES)
    parser.add_argument("--sensitivity-max-k", nargs="+", type=int, default=SENSITIVITY_MAX_K_VALUES)
    parser.add_argument("--xor-drat-max-detected-equations", type=int, default=DEFAULT_XOR_DRAT_MAX_DETECTED_EQUATIONS)
    parser.add_argument("--xor-drat-max-source-clauses", type=int, default=DEFAULT_XOR_DRAT_MAX_SOURCE_CLAUSES)
    parser.add_argument("--zip", default="witnora-core-v0.9.4-official-xor-diagnostic.zip")
    args = parser.parse_args(argv)

    root = Path(args.out_root)
    if root.exists():
        shutil.rmtree(root)
    result = run_diagnostic(
        root,
        cnfgen_path=args.cnfgen_path,
        drat_trim_path=args.drat_trim,
        timeout_seconds=args.timeout_seconds,
        c_values=args.c_values,
        sensitivity_max_k=args.sensitivity_max_k,
        xor_drat_max_detected_equations=args.xor_drat_max_detected_equations,
        xor_drat_max_source_clauses=args.xor_drat_max_source_clauses,
    )
    digest = make_artifact_zip(root, Path(args.zip))
    print(
        stable_json(
            {
                "out_root": str(root),
                "zip": args.zip,
                "zip_sha256": digest,
                "category_summary": result["category_summary"],
                "drat_summary": result["drat_summary"],
                "failures": result["failures"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
