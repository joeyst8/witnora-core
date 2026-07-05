"""Focused Tseitin XOR-to-DRAT diagnostic for Witnora-Core."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any
import zipfile

from .cnfgen_matrix import cnfgen_version
from .dimacs import parse_dimacs
from .independent_check import verify_wcert_raw
from .proof import export_certificate_bundle
from .public_benchmarks import (
    UNSAT_DRAT_EXPORTED_VERIFIED,
    UNSAT_XOR_NATIVE_ONLY,
    find_cnfgen_cli,
)
from .runner import solve_with_xor
from .xor_drat import XOR_ELIM_GAUSSIAN, XOR_ELIM_SPARSE_MIN_FILL, _detected_equations, _sparse_xor_elimination_order

DIAGNOSTIC_VERSION = "0.9.7"
DEFAULT_INSTANCES = ["tseitin_10", "tseitin_15", "tseitin_20", "tseitin_30"]
DEFAULT_C_VALUES = [2, 3, 4]
DEFAULT_CAP_PROFILES = {
    "conservative": {
        "max_row_width": 8,
        "max_proof_clauses": 50000,
        "max_proof_bytes": 5_000_000,
        "timeout_seconds": 120.0,
    },
    "medium": {
        "max_row_width": 14,
        "max_proof_clauses": 100000,
        "max_proof_bytes": 10_000_000,
        "timeout_seconds": 300.0,
    },
    "high": {
        "max_row_width": 16,
        "max_proof_clauses": 250000,
        "max_proof_bytes": 25_000_000,
        "timeout_seconds": 600.0,
    },
    "diagnostic-high": {
        "max_row_width": 18,
        "max_proof_clauses": 500000,
        "max_proof_bytes": 50_000_000,
        "timeout_seconds": 900.0,
    },
}


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
        return proc.stdout.strip() if proc.returncode == 0 else ""

    return {
        "commit": run_git(["rev-parse", "HEAD"]),
        "tag": run_git(["describe", "--tags", "--exact-match"]),
    }


def instance_size(instance_id: str) -> int:
    if not instance_id.startswith("tseitin_"):
        raise ValueError(f"unsupported instance id: {instance_id}")
    return int(instance_id.split("_", 1)[1])


def generate_tseitin(cnfgen: str, instance_id: str, out_path: Path) -> str:
    n = instance_size(instance_id)
    command = [cnfgen, "--seed", str(n), "tseitin", str(n)]
    proc = subprocess.run(command, capture_output=True, text=True, check=False)
    if proc.returncode != 0 or not proc.stdout.strip():
        raise RuntimeError(f"CNFgen failed for {instance_id}: {proc.stderr[:500]}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(proc.stdout, encoding="utf-8", newline="\n")
    return " ".join(command)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def run_attempt(
    *,
    cnfgen: str,
    drat_trim_path: str,
    out_root: Path,
    instance_id: str,
    c: int,
    profile_name: str,
    profile: dict[str, Any],
    detect_xor_max_k: int,
    xor_elim_order: str = XOR_ELIM_GAUSSIAN,
) -> dict[str, Any]:
    started = time.perf_counter()
    dimacs_path = out_root / "generated_dimacs" / f"{instance_id}.cnf"
    generation_command = generate_tseitin(cnfgen, instance_id, dimacs_path)
    original_text = dimacs_path.read_text(encoding="utf-8")
    formula = parse_dimacs(original_text)
    path = solve_with_xor(formula, c=c, detect_cnf_xor=True, detect_xor_max_k=detect_xor_max_k)
    detected = _detected_equations(path)
    sparse_order, sparse_order_stats = _sparse_xor_elimination_order(detected)
    cert_dir = out_root / "certs" / profile_name / xor_elim_order / f"c{c}" / f"{instance_id}.wcert"
    export_certificate_bundle(
        formula,
        path,
        cert_dir,
        original_dimacs_text=original_text,
        export_drat=True,
        export_xor_drat=True,
        drat_trim_path=drat_trim_path,
        xor_drat_max_row_width=int(profile["max_row_width"]),
        xor_drat_max_proof_clauses=int(profile["max_proof_clauses"]),
        xor_drat_max_proof_bytes=int(profile["max_proof_bytes"]),
        xor_drat_timeout_seconds=float(profile["timeout_seconds"]),
        xor_elim_order=xor_elim_order,
    )
    result = load_json(cert_dir / "result.json")
    drat_status = load_json(cert_dir / "drat_status.json")
    xor_drat_status = load_json(cert_dir / "xor_drat_status.json")
    proof = cert_dir / "proof.drat"
    log_dir = out_root / "drat_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{profile_name}_{xor_elim_order}_c{c}_{instance_id}.log"
    log_path.write_text(
        str(drat_status.get("external_checker_stdout_excerpt", ""))
        + "\n"
        + str(drat_status.get("external_checker_stderr_excerpt", "")),
        encoding="utf-8",
        newline="\n",
    )
    independent_dir = out_root / "independent_checks"
    independent_dir.mkdir(parents=True, exist_ok=True)
    independent_path = independent_dir / f"{profile_name}_{xor_elim_order}_c{c}_{instance_id}.json"
    independent_result = verify_wcert_raw(cert_dir)
    independent_path.write_text(stable_json(independent_result), encoding="utf-8", newline="\n")
    public_category = str(result.get("public_category", ""))
    return {
        "instance_id": instance_id,
        "family": "tseitin",
        "c": c,
        "cap_profile": profile_name,
        "xor_elim_order": xor_elim_order,
        "generation_command": generation_command,
        "dimacs_path": str(dimacs_path),
        "certificate_path": str(cert_dir),
        "proof_drat_path": str(proof) if proof.exists() else "",
        "drat_trim_log_path": str(log_path),
        "independent_checker_path": str(independent_path),
        "independent_checker_verified": bool(independent_result.get("verified", False)),
        "status": result.get("logical_status", result.get("status", "")),
        "internal_status": result.get("status", ""),
        "discovery_route": result.get("discovery_route", ""),
        "certification_level": result.get("certification_level", ""),
        "public_category": public_category,
        "xor_drat_status": xor_drat_status.get("xor_drat_status", ""),
        "skip_reason": xor_drat_status.get("skip_reason"),
        "row_width": xor_drat_status.get("row_width"),
        "row_width_initial": xor_drat_status.get("row_width_initial"),
        "row_width_peak": xor_drat_status.get("row_width_peak"),
        "row_width_final_contradiction": xor_drat_status.get("row_width_final_contradiction"),
        "xor_elimination_order": xor_drat_status.get("xor_elimination_order", []),
        "xor_elimination_order_strategy": xor_drat_status.get("xor_elimination_order_strategy"),
        "elimination_order_source": xor_drat_status.get("elimination_order_source"),
        "elimination_order_variables": xor_drat_status.get("elimination_order_variables", []),
        "row_operation_trace_length": len(xor_drat_status.get("row_operation_trace", [])),
        "peak_row_width": xor_drat_status.get("peak_row_width"),
        "sparse_order": sparse_order,
        "sparse_row_width_peak": sparse_order_stats.get("row_width_peak"),
        "sparse_row_width_initial": sparse_order_stats.get("row_width_initial"),
        "sparse_row_width_final_contradiction": sparse_order_stats.get("row_width_final_contradiction"),
        "max_row_width_cap": xor_drat_status.get("max_row_width_cap"),
        "proof_clause_count_estimate": xor_drat_status.get("proof_clause_count_estimate"),
        "proof_clause_count_actual": xor_drat_status.get("proof_clause_count_actual"),
        "max_proof_clause_cap": xor_drat_status.get("max_proof_clause_cap"),
        "proof_clause_max_width": xor_drat_status.get("proof_clause_max_width"),
        "proof_file_size_bytes": xor_drat_status.get("proof_file_size_bytes"),
        "max_proof_bytes": xor_drat_status.get("max_proof_bytes"),
        "internal_rup_status": xor_drat_status.get("internal_rup_status"),
        "proof_generation_runtime_seconds": xor_drat_status.get("proof_generation_runtime_seconds"),
        "internal_rup_runtime_seconds": xor_drat_status.get("internal_rup_runtime_seconds"),
        "drat_trim_status": xor_drat_status.get("drat_trim_status"),
        "drat_trim_runtime_seconds": xor_drat_status.get("drat_trim_runtime_seconds"),
        "original_num_vars": xor_drat_status.get("original_num_vars"),
        "original_num_clauses": xor_drat_status.get("original_num_clauses"),
        "detected_xor_equations": xor_drat_status.get("detected_xor_equations"),
        "max_detected_xor_arity": xor_drat_status.get("max_detected_xor_arity"),
        "external_checker": drat_status.get("external_checker", ""),
        "external_checker_ran": bool(drat_status.get("external_checker_ran", False)),
        "external_checker_verified": bool(drat_status.get("external_checker_verified", False)),
        "false_drat_claim": public_category == UNSAT_DRAT_EXPORTED_VERIFIED
        and not bool(drat_status.get("external_checker_verified", False)),
        "elapsed_seconds": round(time.perf_counter() - started, 6),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = [
        "instance_id",
        "family",
        "c",
        "cap_profile",
        "xor_elim_order",
        "public_category",
        "xor_drat_status",
        "skip_reason",
        "row_width",
        "row_width_initial",
        "row_width_peak",
        "row_width_final_contradiction",
        "xor_elimination_order_strategy",
        "elimination_order_source",
        "row_operation_trace_length",
        "sparse_row_width_peak",
        "max_row_width_cap",
        "proof_clause_count_actual",
        "max_proof_clause_cap",
        "proof_clause_max_width",
        "proof_file_size_bytes",
        "max_proof_bytes",
        "proof_generation_runtime_seconds",
        "internal_rup_runtime_seconds",
        "internal_rup_status",
        "drat_trim_status",
        "drat_trim_runtime_seconds",
        "detected_xor_equations",
        "max_detected_xor_arity",
        "external_checker",
        "external_checker_ran",
        "external_checker_verified",
        "false_drat_claim",
        "certificate_path",
        "proof_drat_path",
        "drat_trim_log_path",
        "independent_checker_path",
        "independent_checker_verified",
        "elapsed_seconds",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    verified = [row for row in rows if row.get("public_category") == UNSAT_DRAT_EXPORTED_VERIFIED]
    native = [row for row in rows if row.get("public_category") == UNSAT_XOR_NATIVE_ONLY]
    gaussian_t15 = [
        row for row in rows
        if row.get("instance_id") == "tseitin_15" and row.get("xor_elim_order") == XOR_ELIM_GAUSSIAN
    ]
    minfill_t15 = [
        row for row in rows
        if row.get("instance_id") == "tseitin_15" and row.get("xor_elim_order") == XOR_ELIM_SPARSE_MIN_FILL
    ]
    minfill_verified = [
        row for row in minfill_t15
        if row.get("public_category") == UNSAT_DRAT_EXPORTED_VERIFIED
    ]
    return {
        "total_profiles_attempted": len(rows),
        "total_tseitin_rows_attempted": len(rows),
        "UNSAT_DRAT_EXPORTED_VERIFIED": len(verified),
        "UNSAT_XOR_NATIVE_ONLY": len(native),
        "XOR_DRAT_SKIPPED_ROW_WIDTH_CAP": sum(1 for row in rows if row.get("xor_drat_status") == "SKIPPED_ROW_WIDTH_CAP"),
        "XOR_DRAT_SKIPPED_PROOF_SIZE_CAP": sum(1 for row in rows if row.get("xor_drat_status") == "SKIPPED_PROOF_SIZE_CAP"),
        "XOR_DRAT_SKIPPED_TIME_CAP": sum(1 for row in rows if row.get("xor_drat_status") == "SKIPPED_TIME_CAP"),
        "INTERNAL_RUP_FAILED": sum(1 for row in rows if row.get("xor_drat_status") == "INTERNAL_RUP_FAILED"),
        "DRAT_TRIM_FAILED": sum(1 for row in rows if row.get("xor_drat_status") == "DRAT_TRIM_FAILED"),
        "false_drat_claims": sum(1 for row in rows if row.get("false_drat_claim")),
        "best_verified_instance": verified[0]["instance_id"] if verified else "",
        "largest_verified_instance": verified[-1]["instance_id"] if verified else "",
        "gaussian_peak_width_tseitin15": gaussian_t15[0].get("row_width_peak") if gaussian_t15 else None,
        "minfill_peak_width_tseitin15": minfill_t15[0].get("row_width_peak") if minfill_t15 else None,
        "gaussian_proof_clause_count_or_cap": gaussian_t15[0].get("proof_clause_count_actual") if gaussian_t15 else None,
        "minfill_proof_clause_count": minfill_verified[0].get("proof_clause_count_actual") if minfill_verified else None,
        "minfill_proof_bytes": minfill_verified[0].get("proof_file_size_bytes") if minfill_verified else None,
        "minfill_drat_trim_runtime": minfill_verified[0].get("drat_trim_runtime_seconds") if minfill_verified else None,
        "tseitin_15_public_category": (
            minfill_verified[0].get("public_category")
            if minfill_verified
            else (minfill_t15[0].get("public_category") if minfill_t15 else "")
        ),
        "tseitin_15_verified_profiles": [
            f"{row['cap_profile']}:{row.get('xor_elim_order', '')}"
            for row in rows
            if row.get("instance_id") == "tseitin_15" and row.get("public_category") == UNSAT_DRAT_EXPORTED_VERIFIED
        ],
        "best_tseitin_15_public_category": next(
            (
                row.get("public_category")
                for row in rows
                if row.get("instance_id") == "tseitin_15" and row.get("public_category") == UNSAT_DRAT_EXPORTED_VERIFIED
            ),
            next((row.get("public_category") for row in rows if row.get("instance_id") == "tseitin_15"), ""),
        ),
        "peak_row_width_by_profile": {
            f"{row['cap_profile']}:{row.get('xor_elim_order', '')}:c{row['c']}:{row['instance_id']}": row.get("row_width_peak", row.get("row_width"))
            for row in rows
        },
        "proof_clause_count_by_profile": {
            f"{row['cap_profile']}:{row.get('xor_elim_order', '')}:c{row['c']}:{row['instance_id']}": row.get("proof_clause_count_actual")
            for row in rows
        },
        "proof_size_by_profile": {
            f"{row['cap_profile']}:{row.get('xor_elim_order', '')}:c{row['c']}:{row['instance_id']}": row.get("proof_file_size_bytes")
            for row in rows
        },
        "skip_reason_by_profile": {
            f"{row['cap_profile']}:{row.get('xor_elim_order', '')}:c{row['c']}:{row['instance_id']}": row.get("skip_reason")
            for row in rows
        },
        "recommended_next_step": _recommended_next_step(rows),
        "proof_size_by_instance": {
            f"{row['cap_profile']}:{row.get('xor_elim_order', '')}:c{row['c']}:{row['instance_id']}": row.get("proof_file_size_bytes")
            for row in rows
            if row.get("proof_file_size_bytes")
        },
        "drat_trim_runtime_by_instance": {
            f"{row['cap_profile']}:{row.get('xor_elim_order', '')}:c{row['c']}:{row['instance_id']}": row.get("drat_trim_runtime_seconds")
            for row in rows
            if row.get("drat_trim_runtime_seconds") is not None
        },
    }


def _recommended_next_step(rows: list[dict[str, Any]]) -> str:
    if any(row.get("instance_id") == "tseitin_15" and row.get("public_category") == UNSAT_DRAT_EXPORTED_VERIFIED for row in rows):
        return "attempt tseitin_20 with the verified cap profile"
    if any(row.get("xor_drat_status") == "SKIPPED_PROOF_SIZE_CAP" for row in rows):
        return "reduce proof generation before raising proof-size caps"
    if any(row.get("xor_drat_status") == "SKIPPED_TIME_CAP" for row in rows):
        return "optimize proof generation before increasing time caps"
    if any(row.get("xor_drat_status") == "SKIPPED_ROW_WIDTH_CAP" for row in rows):
        return "run controlled row-width cap sensitivity"
    return "no next step inferred"


def report_markdown(rows: list[dict[str, Any]], run_summary: dict[str, Any]) -> str:
    lines = [
        "# Witnora-Core v0.9.7 Min-Fill XOR-DRAT Diagnostic",
        "",
        "This is a proof-engineering diagnostic, not a competitive SAT benchmark.",
        "Every verified row must have real drat-trim verification against original.dimacs.",
        "",
        "## Summary",
        "",
    ]
    for key, value in run_summary.items():
        if isinstance(value, dict):
            continue
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Per-Instance Attempts",
            "",
            "| profile | order | c | instance | public_category | xor_drat_status | row_width | sparse_width | proof_clauses | proof_bytes | drat_trim_s | skip_reason |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| {cap_profile} | {xor_elim_order} | {c} | {instance_id} | {public_category} | {xor_drat_status} | "
            "{row_width} | {sparse_row_width_peak} | {proof_clause_count_actual} | {proof_file_size_bytes} | "
            "{drat_trim_runtime_seconds} | {skip_reason} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Elimination Order Comparison",
            "",
            "Sparse/min-fill is deterministic, certificate-recorded, independently replayed, and counted only when proof.drat verifies with real drat-trim.",
            "",
        ]
    )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "Allowed: selected official CNFgen Tseitin detected-CNF XOR contradictions are externally certified only where public_category is UNSAT_DRAT_EXPORTED_VERIFIED and drat-trim verified proof.drat against original.dimacs.",
            "",
            "Forbidden: no parity support claim, no broad XOR extraction claim, no CryptoMiniSat-style claim, no competitive SAT claim, no P vs NP claim, and no HARD or UNKNOWN statuses.",
            "",
        ]
    )
    return "\n".join(lines)


def make_zip(root: Path, zip_path: Path) -> str:
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
    drat_trim_path: str,
    instances: list[str],
    c_values: list[int],
    detect_xor_max_k: int,
    profiles: list[str],
    elim_orders: list[str],
) -> dict[str, Any]:
    cnfgen = find_cnfgen_cli(cnfgen_path)
    if cnfgen is None:
        raise RuntimeError("official CNFgen CLI not found")
    out_root.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for profile_name in profiles:
        profile = DEFAULT_CAP_PROFILES[profile_name]
        for elim_order in elim_orders:
            for c in c_values:
                for instance in instances:
                    rows.append(
                        run_attempt(
                            cnfgen=cnfgen,
                            drat_trim_path=drat_trim_path,
                            out_root=out_root,
                            instance_id=instance,
                            c=c,
                            profile_name=profile_name,
                            profile=profile,
                            detect_xor_max_k=detect_xor_max_k,
                            xor_elim_order=elim_order,
                        )
                    )
    run_summary = summary(rows)
    git = git_metadata()
    manifest = {
        "diagnostic_version": DIAGNOSTIC_VERSION,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "witnora_commit": git.get("commit", ""),
        "witnora_tag": git.get("tag", "") or "uncommitted",
        "cnfgen_path": cnfgen,
        "cnfgen_version": cnfgen_version(cnfgen),
        "drat_trim_path": drat_trim_path,
        "instances": instances,
        "c_values": c_values,
        "detect_xor_max_k": detect_xor_max_k,
        "elim_orders": elim_orders,
        "cap_profiles": {name: DEFAULT_CAP_PROFILES[name] for name in profiles},
    }
    files = {
        "manifest.json": manifest,
        "summary.json": run_summary,
        "per_instance_summary.json": {"rows": rows},
        "environment.json": {
            "python": sys.version.replace("\n", " "),
            "cnfgen_path": cnfgen,
            "cnfgen_version": cnfgen_version(cnfgen),
            "drat_trim_path": drat_trim_path,
        },
    }
    for name, payload in files.items():
        (out_root / name).write_text(stable_json(payload), encoding="utf-8", newline="\n")
    write_csv(out_root / "per_instance_summary.csv", rows)
    report_text = report_markdown(rows, run_summary)
    (out_root / "TSEITIN_XOR_DRAT_DIAGNOSTIC_REPORT.md").write_text(report_text, encoding="utf-8", newline="\n")
    (out_root / "TSEITIN15_XOR_DRAT_SCALING_REPORT.md").write_text(report_text, encoding="utf-8", newline="\n")
    return {"manifest": manifest, "summary": run_summary, "rows": rows}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run focused Tseitin XOR-DRAT diagnostic")
    parser.add_argument("--family", default="tseitin", choices=["tseitin"])
    parser.add_argument("--instances", nargs="+", default=DEFAULT_INSTANCES)
    parser.add_argument("--c-values", nargs="+", type=int, default=DEFAULT_C_VALUES)
    parser.add_argument("--detect-xor-max-k", type=int, default=6)
    parser.add_argument("--xor-drat", action="store_true")
    parser.add_argument("--drat-trim", required=True)
    parser.add_argument("--cnfgen-path")
    parser.add_argument("--profiles", nargs="+", choices=sorted(DEFAULT_CAP_PROFILES), default=["conservative"])
    parser.add_argument(
        "--elim-orders",
        nargs="+",
        choices=[XOR_ELIM_GAUSSIAN, XOR_ELIM_SPARSE_MIN_FILL],
        default=[XOR_ELIM_GAUSSIAN],
    )
    parser.add_argument("--out-root", default="outputs/v0.9.7-minfill-xor-drat")
    parser.add_argument("--zip", default="witnora-core-v0.9.7-minfill-xor-drat.zip")
    args = parser.parse_args(argv)
    if not args.xor_drat:
        raise SystemExit("--xor-drat is required for this diagnostic")
    root = Path(args.out_root)
    if root.exists():
        shutil.rmtree(root)
    result = run_diagnostic(
        root,
        cnfgen_path=args.cnfgen_path,
        drat_trim_path=args.drat_trim,
        instances=args.instances,
        c_values=args.c_values,
        detect_xor_max_k=args.detect_xor_max_k,
        profiles=args.profiles,
        elim_orders=args.elim_orders,
    )
    digest = make_zip(root, Path(args.zip))
    print(stable_json({"out_root": str(root), "zip": args.zip, "zip_sha256": digest, "summary": result["summary"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
