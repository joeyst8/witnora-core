"""Official CNFgen diagnostic matrix runner for Witnora-Core v0.8.4."""

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
from typing import Any, Iterable

from .benchmark_artifact import create_artifact_zip, selected_instances_text
from .public_benchmarks import (
    ERROR,
    NO_COLLAPSE_FOUND,
    PUBLIC_CATEGORIES,
    SOURCE_OFFICIAL_CNFGEN,
    SUITE_NOT_RUN,
    SUITE_RUN,
    TIMEOUT,
    UNSAT_DRAT_EXPORTED_VERIFIED,
    UNSAT_NOT_EXTERNALLY_VERIFIED,
    UNSUPPORTED_DRAT,
    PublicBenchmarkCase,
    find_cnfgen_cli,
    generate_public_markdown_report,
    official_cnfgen_install_instructions,
    run_public_benchmark,
    write_public_csv,
)

MATRIX_VERSION = "0.8.4"
DEFAULT_C_VALUES = [2, 3, 4]
DEFAULT_TIMEOUT_SECONDS = 300.0
DEFAULT_MAX_WIDTH_SEARCH_VARS = 28

REASON_OFFICIAL_CNFGEN_NOT_AVAILABLE = "OFFICIAL_CNFGEN_NOT_AVAILABLE"
REASON_UNSUPPORTED_FAMILY = "OFFICIAL_CNFGEN_FAMILY_NOT_AVAILABLE_OR_FAILED"


def cnfgen_version(cnfgen_path: str | Path | None = None) -> str:
    cli = find_cnfgen_cli(cnfgen_path)
    if cli is None:
        return ""
    proc = subprocess.run([cli, "--version"], capture_output=True, text=True, check=False)
    return (proc.stdout or proc.stderr).strip()


def _command_text(command: list[str]) -> str:
    return " ".join(command)


def _run_cnfgen(command: list[str], output_path: Path) -> tuple[bool, str, str]:
    proc = subprocess.run(command, capture_output=True, text=True, check=False)
    if proc.returncode != 0 or not proc.stdout.strip():
        return False, proc.stdout, proc.stderr
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(proc.stdout, encoding="utf-8")
    return True, proc.stdout, proc.stderr


def family_command_specs(cnfgen_cli: str, family: str) -> list[tuple[str, list[str]]]:
    if family == "pigeonhole":
        return [
            (f"php_{pigeons}_{pigeons - 1}", [cnfgen_cli, "php", str(pigeons), str(pigeons - 1)])
            for pigeons in range(3, 11)
        ]
    if family == "tseitin":
        return [
            (f"tseitin_{n}", [cnfgen_cli, "--seed", str(n), "tseitin", str(n)])
            for n in [10, 15, 20, 30]
        ]
    if family == "parity":
        return [
            (f"parity_{n}", [cnfgen_cli, "--seed", str(n), "parity", str(n)])
            for n in [12, 16, 20]
        ]
    raise ValueError(f"unsupported CNFgen diagnostic family: {family}")


def generate_cnfgen_family_cases(
    family: str,
    generated_dimacs_dir: str | Path,
    *,
    cnfgen_path: str | Path | None = None,
) -> tuple[list[PublicBenchmarkCase], dict[str, Any]]:
    cli = find_cnfgen_cli(cnfgen_path)
    manifest: dict[str, Any] = {
        "family": family,
        "suite_source_type": SOURCE_OFFICIAL_CNFGEN,
        "suite_status": SUITE_NOT_RUN,
        "not_run_reason": REASON_OFFICIAL_CNFGEN_NOT_AVAILABLE,
        "cnfgen_path": cli,
        "cnfgen_version": cnfgen_version(cnfgen_path),
        "generation_commands": [],
        "generation_failures": [],
        "selected_instances": [],
        "dimacs_source_paths": [],
        "instructions": official_cnfgen_install_instructions(),
    }
    if cli is None:
        return [], manifest

    requested = family_command_specs(cli, family)
    cases: list[PublicBenchmarkCase] = []
    out_dir = Path(generated_dimacs_dir)
    for instance_name, command in requested:
        output_path = out_dir / f"{instance_name}.cnf"
        command_text = _command_text(command)
        manifest["generation_commands"].append(command_text)
        ok, stdout, stderr = _run_cnfgen(command, output_path)
        if not ok:
            manifest["generation_failures"].append(
                {
                    "instance_name": instance_name,
                    "command": command_text,
                    "stdout_excerpt": stdout[:500],
                    "stderr_excerpt": stderr[:500],
                }
            )
            continue
        cases.append(
            PublicBenchmarkCase(
                instance_name=instance_name,
                source_suite="cnfgen-official",
                family=family,
                dimacs_text=output_path.read_text(encoding="utf-8"),
                source=str(output_path),
                notes="official CNFgen diagnostic matrix output",
                source_type=SOURCE_OFFICIAL_CNFGEN,
                generation_command=command_text,
                dimacs_source_path=str(output_path),
            )
        )
        manifest["selected_instances"].append(instance_name)
        manifest["dimacs_source_paths"].append(str(output_path))

    if cases:
        manifest["suite_status"] = SUITE_RUN
        manifest["not_run_reason"] = None
        manifest["instance_count"] = len(cases)
    else:
        manifest["not_run_reason"] = REASON_UNSUPPORTED_FAMILY
        manifest["instance_count"] = 0
    return cases, manifest


def _average(values: Iterable[Any]) -> float:
    parsed = [float(value) for value in values if value not in (None, "")]
    return round(sum(parsed) / len(parsed), 6) if parsed else 0.0


def summarize_matrix_run(family: str, c_value: int, data: dict[str, Any]) -> dict[str, Any]:
    results = list(data.get("per_case_results", []))
    summary = dict(data.get("summary", {}))
    category_counts = dict(summary.get("category_counts", {}))
    solved_categories = {"SAT_ASSIGNMENT_VERIFIED", UNSAT_DRAT_EXPORTED_VERIFIED}
    solved = [r for r in results if r.get("public_category") in solved_categories]
    no_collapse = [r for r in results if r.get("public_category") == NO_COLLAPSE_FOUND]
    return {
        "family": family,
        "c_parameter": c_value,
        "suite_status": data.get("suite_status", SUITE_RUN),
        "not_run_reason": data.get("not_run_reason"),
        "total_cases": int(summary.get("total_cases", len(results))),
        **{category: int(category_counts.get(category, 0)) for category in PUBLIC_CATEGORIES},
        "strict_unsat_external_pass": bool(summary.get("strict_unsat_external_pass", True)),
        "externally_verified_unsat_count": int(summary.get("externally_verified_unsat_count", 0)),
        "max_instance_solved": str(solved[-1].get("instance_name", "")) if solved else "",
        "first_no_collapse_instance": str(no_collapse[0].get("instance_name", "")) if no_collapse else "",
        "average_solver_time_seconds": _average(r.get("solver_time_seconds") for r in results),
        "average_drat_trim_time_seconds": _average(r.get("drat_trim_time_seconds") for r in results),
        "average_collapse_path_length": float(summary.get("average_collapse_path_length", 0.0)),
    }


def write_matrix_summary_csv(rows: list[dict[str, Any]], path: str | Path) -> None:
    columns = [
        "family",
        "c_parameter",
        "suite_status",
        "not_run_reason",
        "total_cases",
        *PUBLIC_CATEGORIES,
        "strict_unsat_external_pass",
        "externally_verified_unsat_count",
        "max_instance_solved",
        "first_no_collapse_instance",
        "average_solver_time_seconds",
        "average_drat_trim_time_seconds",
        "average_collapse_path_length",
    ]
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def matrix_markdown(summary: dict[str, Any]) -> str:
    rows = list(summary.get("rows", []))
    lines = [
        "# Witnora-Core v0.8.4 Official CNFgen Diagnostic Matrix",
        "",
        "This is an official CNFgen diagnostic benchmark. It measures the current collapse boundary across formula family and c value.",
        "It is not a solver-performance claim. `NO_COLLAPSE_FOUND` is not hardness.",
        "",
        "## Configuration",
        "",
        f"- CNFgen: {summary.get('cnfgen_version', '')}",
        f"- CNFgen path: {summary.get('cnfgen_path', '')}",
        f"- c values: {', '.join(str(c) for c in summary.get('c_values', []))}",
        f"- timeout_seconds: {summary.get('timeout_seconds', '')}",
        f"- strict_unsat_external: {summary.get('strict_unsat_external', '')}",
        f"- drat-trim path: {summary.get('drat_trim_path', '')}",
        "",
        "## Matrix Counts",
        "",
        "| Family | c | Total | SAT verified | UNSAT drat verified | No collapse | Timeout | Error | Max solved | First no-collapse |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {family} | {c_parameter} | {total_cases} | {SAT_ASSIGNMENT_VERIFIED} | "
            "{UNSAT_DRAT_EXPORTED_VERIFIED} | {NO_COLLAPSE_FOUND} | {TIMEOUT} | {ERROR} | "
            "{max_instance_solved} | {first_no_collapse_instance} |".format(**row)
        )
    lines.extend(["", "## Family Notes", ""])
    for family in ["pigeonhole", "tseitin", "parity"]:
        family_rows = [row for row in rows if row.get("family") == family]
        if not family_rows:
            reason = summary.get("not_run_reasons", {}).get(family, "not run")
            lines.append(f"- `{family}`: NOT_RUN ({reason}).")
            continue
        solved_by_c = {
            str(row.get("c_parameter")): row.get("max_instance_solved", "")
            for row in family_rows
        }
        no_collapse_count = sum(int(row.get(NO_COLLAPSE_FOUND, 0)) for row in family_rows)
        timeout_count = sum(int(row.get(TIMEOUT, 0)) for row in family_rows)
        if family == "pigeonhole":
            lines.append(
                f"- `pigeonhole`: largest solved by c: {json.dumps(solved_by_c, sort_keys=True)}. "
                "This reports a boundary observation only; it does not claim Witnora solves pigeonhole generally."
            )
        elif family == "tseitin":
            lines.append(
                f"- `tseitin`: largest solved by c: {json.dumps(solved_by_c, sort_keys=True)}; "
                f"no-collapse count {no_collapse_count}, timeout count {timeout_count}."
            )
        else:
            lines.append(
                f"- `parity`: largest solved by c: {json.dumps(solved_by_c, sort_keys=True)}; "
                "if these cases do not collapse, the only allowed interpretation is that the current grammar has no XOR/affine route for them."
            )
    lines.extend(
        [
            "",
            "## Claims Allowed / Claims Forbidden",
            "",
            "Allowed: this artifact is an official CNFgen diagnostic matrix and reports strict categories by family and c value.",
            "Forbidden: no broad SAT performance claim, no general pigeonhole claim, no parity/XOR necessity claim, no P vs NP claim, and no HARD/UNKNOWN status.",
            "",
        ]
    )
    return "\n".join(lines)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    _write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _write_drat_logs(root: Path, family: str, c_value: int, data: dict[str, Any]) -> None:
    log_dir = root / "drat_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    for result in data.get("per_case_results", []):
        cert_path = Path(str(result.get("wcert_path", "")))
        status_path = cert_path / "drat_status.json"
        if not status_path.exists():
            continue
        status = json.loads(status_path.read_text(encoding="utf-8"))
        prefix = f"{family}_c{c_value}_{result.get('instance_name', '')}"
        _write_text(log_dir / f"{prefix}.stdout.txt", str(status.get("external_checker_stdout_excerpt", "")))
        _write_text(log_dir / f"{prefix}.stderr.txt", str(status.get("external_checker_stderr_excerpt", "")))


def write_matrix_artifact(
    root: str | Path,
    summary: dict[str, Any],
    *,
    zip_path: str | Path | None = None,
) -> str | None:
    artifact = Path(root)
    artifact.mkdir(parents=True, exist_ok=True)
    _write_json(artifact / "matrix_summary.json", summary)
    write_matrix_summary_csv(list(summary.get("rows", [])), artifact / "matrix_summary.csv")
    _write_text(artifact / "MATRIX_SUMMARY.md", matrix_markdown(summary))
    _write_text(
        artifact / "README.md",
        "# Witnora-Core v0.8.4 CNFgen Diagnostic Benchmark Artifact\n\n"
        "This artifact is separate from the source release. It contains official CNFgen generated DIMACS files, per-run reports, certificates, and strict-category summaries.\n",
    )
    _write_json(artifact / "config.json", dict(summary.get("config", {})))
    _write_json(artifact / "not_run_reasons.json", dict(summary.get("not_run_reasons", {})))
    _write_text(artifact / "commands_run.txt", "\n".join(summary.get("commands_run", [])) + "\n")
    _write_text(
        artifact / "environment.txt",
        "\n".join(
            [
                f"matrix_version: {MATRIX_VERSION}",
                f"created_utc: {datetime.now(timezone.utc).isoformat()}",
                f"python: {sys.version.replace(chr(10), ' ')}",
                f"platform: {platform.platform()}",
                f"machine: {platform.machine()}",
                f"processor: {platform.processor()}",
            ]
        )
        + "\n",
    )
    generated_root = artifact / "generated_dimacs"
    generated_root.mkdir(exist_ok=True)
    for family, manifest in dict(summary.get("families", {})).items():
        family_generated = generated_root / str(family)
        family_generated.mkdir(parents=True, exist_ok=True)
        for source in manifest.get("dimacs_source_paths", []):
            source_path = Path(str(source))
            if source_path.exists():
                shutil.copy2(source_path, family_generated / source_path.name)
    (artifact / "certs").mkdir(exist_ok=True)
    (artifact / "drat_logs").mkdir(exist_ok=True)
    if zip_path is None:
        return None
    return create_artifact_zip(artifact, zip_path)


def run_cnfgen_matrix(
    root: str | Path,
    *,
    families: list[str] | None = None,
    c_values: list[int] | None = None,
    cnfgen_path: str | Path | None = None,
    drat_trim_path: str | Path | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_width_search_vars: int = DEFAULT_MAX_WIDTH_SEARCH_VARS,
    strict_unsat_external: bool = True,
) -> dict[str, Any]:
    root_path = Path(root)
    families = families or ["pigeonhole", "tseitin", "parity"]
    c_values = c_values or list(DEFAULT_C_VALUES)
    cli = find_cnfgen_cli(cnfgen_path)
    summary: dict[str, Any] = {
        "version": MATRIX_VERSION,
        "benchmark_kind": "official_cnfgen_diagnostic_matrix",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "cnfgen_path": cli or "",
        "cnfgen_version": cnfgen_version(cnfgen_path),
        "drat_trim_path": str(drat_trim_path) if drat_trim_path is not None else "",
        "timeout_seconds": timeout_seconds,
        "max_width_search_vars": max_width_search_vars,
        "strict_unsat_external": strict_unsat_external,
        "families": {},
        "c_values": c_values,
        "rows": [],
        "not_run_reasons": {},
        "commands_run": [],
        "config": {
            "families": families,
            "c_values": c_values,
            "timeout_seconds": timeout_seconds,
            "max_width_search_vars": max_width_search_vars,
            "strict_unsat_external": strict_unsat_external,
            "drat_trim_path": str(drat_trim_path) if drat_trim_path is not None else "",
        },
    }
    for family in families:
        family_root = root_path / family
        generated_dir = family_root / "generated_dimacs"
        cases, manifest = generate_cnfgen_family_cases(
            family,
            generated_dir,
            cnfgen_path=cnfgen_path,
        )
        summary["families"][family] = manifest
        summary["commands_run"].extend(manifest.get("generation_commands", []))
        if not cases:
            reason = str(manifest.get("not_run_reason", REASON_UNSUPPORTED_FAMILY))
            summary["not_run_reasons"][family] = reason
            for c_value in c_values:
                row = {
                    "family": family,
                    "c_parameter": c_value,
                    "suite_status": SUITE_NOT_RUN,
                    "not_run_reason": reason,
                    "total_cases": 0,
                    **{category: 0 for category in PUBLIC_CATEGORIES},
                    "strict_unsat_external_pass": True,
                    "externally_verified_unsat_count": 0,
                    "max_instance_solved": "",
                    "first_no_collapse_instance": "",
                    "average_solver_time_seconds": 0.0,
                    "average_drat_trim_time_seconds": 0.0,
                    "average_collapse_path_length": 0.0,
                }
                summary["rows"].append(row)
            continue
        for c_value in c_values:
            run_root = family_root / f"c{c_value}"
            certs_dir = run_root / "certs"
            data = run_public_benchmark(
                cases,
                c_value,
                timeout_seconds=timeout_seconds,
                max_width_search_vars=max_width_search_vars,
                strict_unsat_external=strict_unsat_external,
                drat_trim_path=drat_trim_path,
                export_certs_dir=certs_dir,
                suite_name=f"cnfgen-official-{family}",
                suite_source_type=SOURCE_OFFICIAL_CNFGEN,
                suite_status=SUITE_RUN,
            )
            data["generation_manifest"] = manifest
            run_root.mkdir(parents=True, exist_ok=True)
            _write_json(run_root / "results.json", data)
            write_public_csv(data, run_root / "results.csv")
            _write_text(run_root / "REPORT.md", generate_public_markdown_report(data))
            _write_text(run_root / "selected_instances.txt", selected_instances_text(data))
            _write_drat_logs(root_path, family, c_value, data)
            summary["rows"].append(summarize_matrix_run(family, c_value, data))
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run official CNFgen diagnostic matrix")
    parser.add_argument("--out-root", default="outputs/v0.8.4-cnfgen-diagnostic")
    parser.add_argument("--families", nargs="+", default=["pigeonhole", "tseitin", "parity"])
    parser.add_argument("--c-values", nargs="+", type=int, default=DEFAULT_C_VALUES)
    parser.add_argument("--cnfgen-path")
    parser.add_argument("--drat-trim")
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--max-width-search-vars", type=int, default=DEFAULT_MAX_WIDTH_SEARCH_VARS)
    parser.add_argument("--strict-unsat-external", action="store_true")
    parser.add_argument("--zip", dest="zip_path", default="witnora-core-v0.8.4-cnfgen-diagnostic-benchmark.zip")
    args = parser.parse_args(argv)

    summary = run_cnfgen_matrix(
        args.out_root,
        families=args.families,
        c_values=args.c_values,
        cnfgen_path=args.cnfgen_path,
        drat_trim_path=args.drat_trim,
        timeout_seconds=args.timeout_seconds,
        max_width_search_vars=args.max_width_search_vars,
        strict_unsat_external=args.strict_unsat_external,
    )
    write_matrix_artifact(args.out_root, summary, zip_path=args.zip_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
