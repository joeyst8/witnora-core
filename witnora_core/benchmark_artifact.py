"""Benchmark artifact writer for public Witnora benchmark runs."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import platform
from pathlib import Path
import shutil
import sys
from typing import Any
import zipfile

from .public_benchmarks import (
    ERROR,
    NO_COLLAPSE_FOUND,
    PUBLIC_CATEGORIES,
    TIMEOUT,
    UNSAT_DRAT_EXPORTED_VERIFIED,
    UNSAT_NOT_EXTERNALLY_VERIFIED,
    UNSAT_XOR_NATIVE_NOT_DRAT,
    UNSUPPORTED_DRAT,
    generate_public_markdown_report,
    write_public_csv,
)

ARTIFACT_VERSION = "0.9.0"
ARTIFACT_DIR_NAME = "v0.9.0-public-benchmark"


def strict_verification_summary(data: dict[str, Any]) -> dict[str, Any]:
    summary = dict(data.get("summary", {}))
    results = list(data.get("per_case_results", []))
    uncertified = [
        result
        for result in results
        if result.get("public_category") in {UNSAT_NOT_EXTERNALLY_VERIFIED, UNSUPPORTED_DRAT, UNSAT_XOR_NATIVE_NOT_DRAT}
    ]
    return {
        "artifact_version": ARTIFACT_VERSION,
        "strict_unsat_external_pass": bool(data.get("strict_unsat_external_pass", False)),
        "strict_unsat_external_failures": list(data.get("strict_unsat_external_failures", [])),
        "unsat_total": int(summary.get("unsat_total", 0)),
        "drat_trim_verified_unsat_count": int(summary.get("externally_verified_unsat_count", 0)),
        "unverified_unsat_count": int(summary.get("unverified_unsat_count", 0)),
        "unsupported_drat_count": int(summary.get("unsupported_drat_count", 0)),
        "xor_native_unsat_count": int(summary.get("xor_native_unsat_count", 0)),
        "certified_unsat_rule": (
            "Only UNSAT_DRAT_EXPORTED_VERIFIED counts as externally certified UNSAT; "
            "UNSAT_NOT_EXTERNALLY_VERIFIED, UNSUPPORTED_DRAT, and UNSAT_XOR_NATIVE_NOT_DRAT are not aggregated with it."
        ),
        "uncertified_unsat_instances": [
            {
                "instance_name": result.get("instance_name", ""),
                "public_category": result.get("public_category", ""),
                "drat_export_status": result.get("drat_export_status", ""),
                "external_checker": result.get("external_checker", ""),
                "external_checker_verified": bool(result.get("external_checker_verified", False)),
                "error_message": result.get("error_message", ""),
            }
            for result in uncertified
        ],
    }


def selected_instances_text(data: dict[str, Any]) -> str:
    cases = list(data.get("cases", []))
    results_by_name = {
        str(result.get("instance_name", "")): result for result in data.get("per_case_results", [])
    }
    lines = [
        "instance_name\tsource_suite\tfamily\tsource_type\tsource\tgeneration_command\tdimacs_source_path\tpublic_category\tstatus",
    ]
    for case in cases:
        name = str(case.get("instance_name", ""))
        result = results_by_name.get(name, {})
        lines.append(
            "\t".join(
                [
                    name,
                    str(case.get("source_suite", "")),
                    str(case.get("family", "")),
                    str(case.get("source_type", "")),
                    str(case.get("source", "")),
                    str(case.get("generation_command", "")),
                    str(case.get("dimacs_source_path", "")),
                    str(result.get("public_category", "")),
                    str(result.get("status", "")),
                ]
            )
        )
    return "\n".join(lines) + "\n"


def environment_text(config: dict[str, Any]) -> str:
    lines = [
        f"artifact_version: {ARTIFACT_VERSION}",
        f"created_utc: {datetime.now(timezone.utc).isoformat()}",
        f"python: {sys.version.replace(chr(10), ' ')}",
        f"platform: {platform.platform()}",
        f"machine: {platform.machine()}",
        f"processor: {platform.processor()}",
        f"drat_trim_path: {config.get('drat_trim_path', '')}",
        "memory_measurement: null",
        "memory_measurement_note: memory was not measured by the v0.9.0 artifact runner",
    ]
    return "\n".join(lines) + "\n"


def artifact_readme_text(config: dict[str, Any], sources_not_run: list[dict[str, str]]) -> str:
    lines = [
        "# Witnora-Core v0.9.0 Public Benchmark Artifact",
        "",
        "This artifact is separate from the Witnora source release archive.",
        "It contains benchmark outputs, certificates, DRAT proof files where exported, and summary reports.",
        "",
        "UNSAT is counted as externally certified only in category `UNSAT_DRAT_EXPORTED_VERIFIED`,",
        "which requires a `proof.drat` file accepted by real `drat-trim`.",
        "",
        "## Configuration",
        "",
        "```json",
        json.dumps(config, indent=2, sort_keys=True),
        "```",
        "",
        "## Source Suites Not Run",
        "",
    ]
    if sources_not_run:
        for source in sources_not_run:
            lines.append(f"- {source.get('suite', '')}: {source.get('reason', '')}")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Files",
            "",
            "- `config.json`: benchmark configuration",
            "- `benchmark_manifest.json`: official suite/run manifest",
            "- `results.json`: raw benchmark JSON",
            "- `results.csv`: per-instance CSV",
            "- `REPORT.md`: Markdown report",
            "- `selected_instances.txt`: exact selected cases",
            "- `strict_verification_summary.json`: strict UNSAT external verification summary",
            "- `environment.txt`: execution environment",
            "- `certs/`: per-instance certificate bundles",
            "- `drat_logs/`: extracted `drat-trim` stdout/stderr excerpts from certificate metadata",
            "- `generated_dimacs/`: generated official CNFgen DIMACS files when applicable",
            "- `raw_outputs/`: command outputs or placeholder directory for raw logs",
            "",
        ]
    )
    return "\n".join(lines)


def benchmark_manifest(
    data: dict[str, Any],
    config: dict[str, Any],
    sources_not_run: list[dict[str, str]],
) -> dict[str, Any]:
    cases = list(data.get("cases", []))
    return {
        "witnora_version": str(config.get("witnora_version", ARTIFACT_VERSION)),
        "commit": str(config.get("commit", "")),
        "tag": str(config.get("tag", "")),
        "benchmark_run_id": str(config.get("benchmark_run_id", "")),
        "run_timestamp": str(config.get("created_utc", data.get("timestamp", ""))),
        "suite_name": str(config.get("suite_name", data.get("suite_name", ""))),
        "suite_source_type": str(config.get("suite_source_type", data.get("suite_source_type", ""))),
        "suite_status": str(config.get("suite_status", data.get("suite_status", "RUN"))),
        "not_run_reason": config.get("not_run_reason", data.get("not_run_reason")),
        "instance_count": len(cases),
        "selected_instances": [case.get("instance_name", "") for case in cases],
        "generation_commands": [
            case.get("generation_command", "")
            for case in cases
            if case.get("generation_command")
        ],
        "dimacs_source_paths": [
            case.get("dimacs_source_path") or case.get("source", "")
            for case in cases
            if case.get("dimacs_source_path") or case.get("source")
        ],
        "drat_trim_path": str(config.get("drat_trim_path", data.get("drat_trim_path", ""))),
        "strict_unsat_external": bool(config.get("strict_unsat_external", data.get("strict_unsat_external", False))),
        "c_parameter": int(config.get("c_parameter", data.get("c_parameter", 0))),
        "timeout_seconds": config.get("timeout_seconds", data.get("timeout_seconds")),
        "max_instances": config.get("max_instances"),
        "max_width_search_vars": config.get("max_width_search_vars", data.get("max_width_search_vars")),
        "sources_not_run": sources_not_run,
    }


def enhanced_report_text(
    data: dict[str, Any],
    config: dict[str, Any],
    sources_not_run: list[dict[str, str]],
    benchmark_commands: list[str],
) -> str:
    base = generate_public_markdown_report(data)
    lines = [
        base.rstrip(),
        "",
        "## Source Suites Used",
    ]
    suites = sorted({str(result.get("source_suite", "")) for result in data.get("per_case_results", [])})
    for suite in suites:
        lines.append(f"- {suite}")
    lines.append("")
    lines.append("## Source Suites Not Run And Why")
    if sources_not_run:
        for source in sources_not_run:
            lines.append(f"- {source.get('suite', '')}: {source.get('reason', '')}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Reproduction Commands")
    if benchmark_commands:
        lines.append("```bash")
        lines.extend(benchmark_commands)
        lines.append("```")
    else:
        lines.append("No commands recorded.")
    lines.append("")
    lines.append("## Artifact Configuration")
    lines.append("```json")
    lines.append(json.dumps(config, indent=2, sort_keys=True))
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def write_drat_logs(artifact_dir: str | Path, data: dict[str, Any]) -> list[str]:
    artifact = Path(artifact_dir)
    log_dir = artifact / "drat_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for result in data.get("per_case_results", []):
        if result.get("public_category") != UNSAT_DRAT_EXPORTED_VERIFIED:
            continue
        wcert = Path(str(result.get("wcert_path", "")))
        status_path = wcert / "drat_status.json"
        if not status_path.exists():
            continue
        status = json.loads(status_path.read_text(encoding="utf-8"))
        stem = str(result.get("instance_name", "unsat")).replace("/", "_").replace("\\", "_")
        stdout_path = log_dir / f"{stem}.stdout.txt"
        stderr_path = log_dir / f"{stem}.stderr.txt"
        stdout_path.write_text(str(status.get("external_checker_stdout_excerpt", "")), encoding="utf-8")
        stderr_path.write_text(str(status.get("external_checker_stderr_excerpt", "")), encoding="utf-8")
        written.extend([str(stdout_path), str(stderr_path)])
    return written


def write_benchmark_artifact(
    artifact_dir: str | Path,
    data: dict[str, Any],
    *,
    config: dict[str, Any],
    sources_not_run: list[dict[str, str]] | None = None,
    benchmark_commands: list[str] | None = None,
) -> dict[str, Any]:
    artifact = Path(artifact_dir)
    artifact.mkdir(parents=True, exist_ok=True)
    (artifact / "certs").mkdir(parents=True, exist_ok=True)
    (artifact / "drat_logs").mkdir(parents=True, exist_ok=True)
    (artifact / "generated_dimacs").mkdir(parents=True, exist_ok=True)
    (artifact / "raw_outputs").mkdir(parents=True, exist_ok=True)

    sources_not_run = list(sources_not_run or [])
    benchmark_commands = list(benchmark_commands or [])
    full_config = dict(config)
    full_config.setdefault("artifact_version", ARTIFACT_VERSION)
    full_config.setdefault("created_utc", datetime.now(timezone.utc).isoformat())
    full_config["sources_not_run"] = sources_not_run
    full_config["benchmark_commands"] = benchmark_commands

    (artifact / "config.json").write_text(
        json.dumps(full_config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest = benchmark_manifest(data, full_config, sources_not_run)
    (artifact / "benchmark_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (artifact / "results.json").write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_public_csv(data, artifact / "results.csv")
    (artifact / "REPORT.md").write_text(
        enhanced_report_text(data, full_config, sources_not_run, benchmark_commands),
        encoding="utf-8",
    )
    (artifact / "selected_instances.txt").write_text(selected_instances_text(data), encoding="utf-8")
    (artifact / "environment.txt").write_text(environment_text(full_config), encoding="utf-8")
    strict_summary = strict_verification_summary(data)
    (artifact / "strict_verification_summary.json").write_text(
        json.dumps(strict_summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (artifact / "version.txt").write_text(f"Witnora-Core v{ARTIFACT_VERSION}\n", encoding="utf-8")
    (artifact / "README.md").write_text(
        artifact_readme_text(full_config, sources_not_run),
        encoding="utf-8",
    )
    drat_logs = write_drat_logs(artifact, data)
    return {
        "artifact_dir": str(artifact),
        "benchmark_manifest": manifest,
        "strict_verification_summary": strict_summary,
        "drat_logs": drat_logs,
    }


def create_artifact_zip(artifact_dir: str | Path, zip_path: str | Path) -> str:
    artifact = Path(artifact_dir)
    zip_target = Path(zip_path)
    zip_target.parent.mkdir(parents=True, exist_ok=True)
    if zip_target.exists():
        zip_target.unlink()
    if artifact.parent.name == "outputs":
        prefix = Path("outputs") / artifact.name
    else:
        prefix = Path(artifact.name)
    with zipfile.ZipFile(zip_target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(artifact.rglob("*")):
            if path.is_dir():
                continue
            if path.resolve() == zip_target.resolve():
                continue
            rel = prefix / path.relative_to(artifact)
            archive.write(path, rel.as_posix())
    return str(zip_target)


def copy_certs_into_artifact(source_certs_dir: str | Path, artifact_dir: str | Path) -> None:
    source = Path(source_certs_dir)
    target = Path(artifact_dir) / "certs"
    target.mkdir(parents=True, exist_ok=True)
    if not source.exists() or source.resolve() == target.resolve():
        return
    for item in sorted(source.iterdir()):
        dest = target / item.name
        if item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write a Witnora public benchmark artifact")
    parser.add_argument("results_json")
    parser.add_argument("--artifact-dir", default=f"outputs/{ARTIFACT_DIR_NAME}")
    parser.add_argument("--zip", dest="zip_path")
    parser.add_argument("--config", help="optional config JSON to merge")
    args = parser.parse_args(argv)

    data = json.loads(Path(args.results_json).read_text(encoding="utf-8"))
    config = {}
    if args.config:
        config.update(json.loads(Path(args.config).read_text(encoding="utf-8")))
    write_benchmark_artifact(args.artifact_dir, data, config=config)
    if args.zip_path:
        create_artifact_zip(args.artifact_dir, args.zip_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
