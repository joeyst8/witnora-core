"""Public benchmark harness with strict certification categories."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import gzip
import json
import multiprocessing
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import traceback
from typing import Any, Iterable

from .benchmark import (
    WIDTH_SKIPPED_SIZE_CAP,
    structural_metrics,
    width_order_measurement,
)
from .certificate import NO_COLLAPSE, SAT, UNSAT, XOR_UNSAT_NATIVE
from .cnf import CNFFormula
from .dimacs import parse_dimacs
from .families import (
    blocked_clique_collapse_family,
    bounded_treewidth_chain_family,
    random_3sat_family,
)
from .proof import export_certificate_bundle
from .runner import solve
from .simplify import simplify

SAT_ASSIGNMENT_VERIFIED = "SAT_ASSIGNMENT_VERIFIED"
UNSAT_DRAT_EXPORTED_VERIFIED = "UNSAT_DRAT_EXPORTED_VERIFIED"
UNSAT_NOT_EXTERNALLY_VERIFIED = "UNSAT_NOT_EXTERNALLY_VERIFIED"
UNSUPPORTED_DRAT = "UNSUPPORTED_DRAT"
UNSAT_XOR_NATIVE_ONLY = "UNSAT_XOR_NATIVE_ONLY"
UNSAT_XOR_NATIVE_NOT_DRAT = UNSAT_XOR_NATIVE_ONLY
NO_COLLAPSE_FOUND = "NO_COLLAPSE_FOUND"
TIMEOUT = "TIMEOUT"
ERROR = "ERROR"

CERTIFICATION_SAT_ASSIGNMENT = "SAT_ASSIGNMENT_VERIFIED"
CERTIFICATION_EXTERNAL_DRAT = "EXTERNAL_DRAT_VERIFIED"
CERTIFICATION_NATIVE_XOR = "NATIVE_XOR_ONLY"
CERTIFICATION_NOT_EXTERNAL = "NOT_EXTERNALLY_VERIFIED"

DISCOVERY_XOR_NATIVE = "XOR_NATIVE_CONTRADICTION"
DISCOVERY_XOR_SIDECAR = "XOR_SIDECAR_CONTRADICTION"

SOURCE_OFFICIAL_CNFGEN = "OFFICIAL_CNFGEN"
SOURCE_SATLIB_DIRECTORY = "SATLIB_DIRECTORY"
SOURCE_SATCOMP_DIRECTORY = "SATCOMP_DIRECTORY"
SOURCE_BUILT_IN_DEMO = "BUILT_IN_DEMO"

SUITE_RUN = "RUN"
SUITE_NOT_RUN = "NOT_RUN"
REASON_OFFICIAL_CNFGEN_NOT_AVAILABLE = "OFFICIAL_CNFGEN_NOT_AVAILABLE"
REASON_SATLIB_DIRECTORY_NOT_PROVIDED = "SATLIB_DIRECTORY_NOT_PROVIDED"
REASON_SATCOMP_DIRECTORY_NOT_PROVIDED = "SATCOMP_DIRECTORY_NOT_PROVIDED"
REASON_DIMACS_DIRECTORY_NOT_FOUND = "DIMACS_DIRECTORY_NOT_FOUND"
REASON_NO_SUPPORTED_CNFGEN_COMMANDS_SUCCEEDED = "NO_SUPPORTED_CNFGEN_COMMANDS_SUCCEEDED"

PUBLIC_CATEGORIES = [
    SAT_ASSIGNMENT_VERIFIED,
    UNSAT_DRAT_EXPORTED_VERIFIED,
    UNSAT_XOR_NATIVE_ONLY,
    UNSAT_NOT_EXTERNALLY_VERIFIED,
    UNSUPPORTED_DRAT,
    NO_COLLAPSE_FOUND,
    TIMEOUT,
    ERROR,
]

PUBLIC_CSV_COLUMNS = [
    "instance_name",
    "source_suite",
    "family",
    "public_category",
    "status",
    "internal_status",
    "discovery_route",
    "certification_level",
    "final_class",
    "c_parameter",
    "original_num_vars",
    "original_num_clauses",
    "post_s_num_vars",
    "post_s_num_clauses",
    "original_max_clause_width",
    "post_s_max_clause_width",
    "original_clique_lower_bound",
    "post_s_width_order_status",
    "collapse_path_length",
    "num_bce_removed",
    "num_ple_assignments",
    "num_up_assignments",
    "num_subsumed_clauses",
    "num_vars_eliminated",
    "solver_time_seconds",
    "drat_export_time_seconds",
    "drat_trim_time_seconds",
    "total_time_seconds",
    "certificate_hash",
    "wcert_path",
    "proof_drat_path",
    "drat_export_status",
    "external_checker",
    "external_checker_ran",
    "external_checker_verified",
    "external_drat",
    "drat_claim",
    "proof_base",
    "strict_unsat_external_pass",
    "error_message",
]

_DRAT_TRIM_TIME_PATTERN = re.compile(r"verification time:\s*([0-9]+(?:\.[0-9]+)?)\s*seconds", re.IGNORECASE)


@dataclass(frozen=True)
class PublicBenchmarkCase:
    instance_name: str
    source_suite: str
    family: str
    dimacs_text: str
    source: str
    notes: str = ""
    source_type: str = SOURCE_BUILT_IN_DEMO
    generation_command: str = ""
    dimacs_source_path: str = ""

    def to_payload(self) -> dict[str, str]:
        return {
            "instance_name": self.instance_name,
            "source_suite": self.source_suite,
            "family": self.family,
            "dimacs_text": self.dimacs_text,
            "source": self.source,
            "notes": self.notes,
            "source_type": self.source_type,
            "generation_command": self.generation_command,
            "dimacs_source_path": self.dimacs_source_path,
        }

    def to_dict(self) -> dict[str, str]:
        return self.to_payload()


def _formula_to_dimacs(formula: CNFFormula) -> str:
    return formula.canonical_dimacs()


def _pigeonhole_formula(pigeons: int, holes: int) -> CNFFormula:
    def var(pigeon: int, hole: int) -> int:
        return (pigeon - 1) * holes + hole

    clauses: list[list[int]] = []
    for pigeon in range(1, pigeons + 1):
        clauses.append([var(pigeon, hole) for hole in range(1, holes + 1)])
    for hole in range(1, holes + 1):
        for p1 in range(1, pigeons + 1):
            for p2 in range(p1 + 1, pigeons + 1):
                clauses.append([-var(p1, hole), -var(p2, hole)])
    return CNFFormula.from_raw_clauses(clauses)


def _parity_pair_formula(name: str, rhs: int) -> tuple[str, CNFFormula]:
    # Two-variable XOR encoded as CNF. rhs=0 means x == y, rhs=1 means x != y.
    if rhs == 0:
        clauses = [[1, -2], [-1, 2]]
    else:
        clauses = [[1, 2], [-1, -2]]
    return name, CNFFormula.from_raw_clauses(clauses)


def cnfgen_small_cases() -> list[PublicBenchmarkCase]:
    """Small built-in demo suite without requiring network or cnfgen."""

    formulas: list[tuple[str, str, CNFFormula, str]] = [
        ("php_2_1", "pigeonhole", _pigeonhole_formula(2, 1), "crafted pigeonhole"),
        ("php_3_2", "pigeonhole", _pigeonhole_formula(3, 2), "crafted pigeonhole"),
        ("php_4_3", "pigeonhole", _pigeonhole_formula(4, 3), "crafted pigeonhole"),
        ("blocked_clique_n5", "blocked_clique", blocked_clique_collapse_family(5), "strictness family"),
        ("blocked_clique_n8", "blocked_clique", blocked_clique_collapse_family(8), "strictness family"),
        ("bounded_chain_n5", "bounded_treewidth_chain", bounded_treewidth_chain_family(5), "bounded width"),
        ("bounded_chain_n7", "bounded_treewidth_chain", bounded_treewidth_chain_family(7), "bounded width"),
        ("random_3sat_seed13", "random_3sat", random_3sat_family(8, 24, 13), "deterministic no-collapse probe"),
        ("parity_equal_pair", "parity", _parity_pair_formula("parity_equal_pair", 0)[1], "crafted parity"),
        ("parity_unequal_pair", "parity", _parity_pair_formula("parity_unequal_pair", 1)[1], "crafted parity"),
    ]
    cases: list[PublicBenchmarkCase] = []
    for name, family, formula, notes in formulas:
        cases.append(
            PublicBenchmarkCase(
                instance_name=name,
                source_suite="cnfgen-small",
                family=family,
                dimacs_text=_formula_to_dimacs(formula),
                source="generated:built_in_demo",
                notes=notes + "; built into Witnora for harness validation only",
                source_type=SOURCE_BUILT_IN_DEMO,
            )
        )
    return cases


def demo_cnfgen_artifact_cases() -> list[PublicBenchmarkCase]:
    """Larger built-in demo suite for harness validation.

    This is not official CNFgen output and must not be presented as external
    benchmark evidence.
    """

    formulas: list[tuple[str, str, CNFFormula, str]] = []
    for pigeons in range(3, 11):
        holes = pigeons - 1
        formulas.append(
            (
                f"php_{pigeons}_{holes}",
                "pigeonhole",
                _pigeonhole_formula(pigeons, holes),
                "built-in demo pigeonhole; harness validation only",
            )
        )
    for n in [5, 8, 12, 16, 20]:
        formulas.append(
            (
                f"blocked_clique_n{n}",
                "blocked_clique",
                blocked_clique_collapse_family(n),
                "built-in demo blocked clique collapse family; harness validation only",
            )
        )
    for n in [5, 7, 9]:
        formulas.append(
            (
                f"bounded_chain_n{n}",
                "bounded_treewidth_chain",
                bounded_treewidth_chain_family(n),
                "built-in demo bounded-treewidth chain; harness validation only",
            )
        )
    for n_vars, n_clauses, seed in [(8, 24, 13), (12, 42, 17), (16, 64, 19)]:
        formulas.append(
            (
                f"random_3sat_v{n_vars}_c{n_clauses}_s{seed}",
                "random_3sat",
                random_3sat_family(n_vars, n_clauses, seed),
                "built-in demo deterministic random 3-SAT no-collapse probe",
            )
        )
    for name, rhs in [("parity_equal_pair", 0), ("parity_unequal_pair", 1)]:
        _unused_name, formula = _parity_pair_formula(name, rhs)
        formulas.append((name, "parity", formula, "built-in demo two-variable parity encoding"))

    cases: list[PublicBenchmarkCase] = []
    for name, family, formula, notes in formulas:
        cases.append(
            PublicBenchmarkCase(
                instance_name=name,
                source_suite="demo-cnfgen-artifact",
                family=family,
                dimacs_text=_formula_to_dimacs(formula),
                source="generated:built_in_demo_v0.9.1",
                notes=notes + "; this suite is built into Witnora and is for harness validation only",
                source_type=SOURCE_BUILT_IN_DEMO,
            )
        )
    return cases


def find_cnfgen_cli(provided_path: str | Path | None = None) -> str | None:
    if provided_path is not None:
        candidate = Path(provided_path)
        return str(candidate) if candidate.is_file() else None
    return shutil.which("cnfgen")


def official_cnfgen_install_instructions() -> str:
    return (
        "Official CNFgen CLI was not found. Install it with `pip install cnfgen` "
        "or from the official CNFgen source, then rerun with --public-suite cnfgen-official."
    )


def _run_cnfgen_command(command: list[str], output_path: Path) -> tuple[bool, str, str]:
    proc = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return False, proc.stdout, proc.stderr
    output_path.write_text(proc.stdout, encoding="utf-8")
    return True, proc.stdout, proc.stderr


def official_cnfgen_cases(
    generated_dimacs_dir: str | Path,
    *,
    cnfgen_path: str | Path | None = None,
    max_instances: int | None = None,
) -> tuple[list[PublicBenchmarkCase], dict[str, Any]]:
    """Generate deterministic formulas with an official CNFgen CLI if present.

    The command surface of CNFgen can vary by installed version. v0.9.1 uses
    conservative command attempts and records every command in the manifest. It
    does not silently fall back to built-in demo formulas.
    """

    cli = find_cnfgen_cli(cnfgen_path)
    manifest: dict[str, Any] = {
        "suite_name": "cnfgen-official",
        "suite_source_type": SOURCE_OFFICIAL_CNFGEN,
        "suite_status": SUITE_NOT_RUN,
        "not_run_reason": REASON_OFFICIAL_CNFGEN_NOT_AVAILABLE,
        "cnfgen_path": cli,
        "generation_commands": [],
        "dimacs_source_paths": [],
        "selected_instances": [],
        "instructions": official_cnfgen_install_instructions(),
    }
    if cli is None:
        return [], manifest

    out_dir = Path(generated_dimacs_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    requested: list[tuple[str, str, list[str]]] = []
    for pigeons in range(3, 11):
        holes = pigeons - 1
        name = f"php_{pigeons}_{holes}"
        requested.append((name, "pigeonhole", [cli, "php", str(pigeons), str(holes)]))

    cases: list[PublicBenchmarkCase] = []
    failures: list[dict[str, str]] = []
    for name, family, command in requested:
        if max_instances is not None and len(cases) >= max_instances:
            break
        output_path = out_dir / f"{name}.cnf"
        ok, stdout, stderr = _run_cnfgen_command(command, output_path)
        command_text = " ".join(command)
        manifest["generation_commands"].append(command_text)
        if not ok:
            failures.append(
                {
                    "instance_name": name,
                    "command": command_text,
                    "stdout_excerpt": stdout[:500],
                    "stderr_excerpt": stderr[:500],
                }
            )
            continue
        dimacs_text = output_path.read_text(encoding="utf-8")
        cases.append(
            PublicBenchmarkCase(
                instance_name=name,
                source_suite="cnfgen-official",
                family=family,
                dimacs_text=dimacs_text,
                source=str(output_path),
                notes="official CNFgen CLI output",
                source_type=SOURCE_OFFICIAL_CNFGEN,
                generation_command=command_text,
                dimacs_source_path=str(output_path),
            )
        )
        manifest["dimacs_source_paths"].append(str(output_path))
        manifest["selected_instances"].append(name)

    if cases:
        manifest["suite_status"] = SUITE_RUN
        manifest["not_run_reason"] = None
        manifest["instance_count"] = len(cases)
    else:
        manifest["not_run_reason"] = REASON_NO_SUPPORTED_CNFGEN_COMMANDS_SUCCEEDED
        manifest["instance_count"] = 0
    manifest["generation_failures"] = failures
    return cases, manifest


def dimacs_dir_cases(
    dimacs_dir: str | Path,
    *,
    source_suite: str = "dimacs-dir",
    source_type: str = "DIMACS_DIRECTORY",
    max_instances: int | None = None,
) -> list[PublicBenchmarkCase]:
    root = Path(dimacs_dir)
    paths = sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and (
            path.suffix.lower() in {".cnf", ".dimacs"}
            or path.name.lower().endswith((".cnf.gz", ".dimacs.gz"))
        )
    )
    if max_instances is not None:
        paths = paths[:max_instances]
    return [
        PublicBenchmarkCase(
            instance_name=path.stem,
            source_suite=source_suite,
            family="dimacs",
            dimacs_text=read_dimacs_text(path),
            source=str(path),
            notes="user-provided public DIMACS directory",
            source_type=source_type,
            dimacs_source_path=str(path),
        )
        for path in paths
    ]


def read_dimacs_text(path: str | Path) -> str:
    source = Path(path)
    if source.name.lower().endswith(".gz"):
        with gzip.open(source, "rt", encoding="utf-8") as handle:
            return handle.read()
    return source.read_text(encoding="utf-8")


def selected_dimacs_paths(dimacs_dir: str | Path, max_instances: int | None = None) -> list[Path]:
    root = Path(dimacs_dir)
    paths = sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and (
            path.suffix.lower() in {".cnf", ".dimacs"}
            or path.name.lower().endswith((".cnf.gz", ".dimacs.gz"))
        )
    )
    return paths[:max_instances] if max_instances is not None else paths


def missing_suite_data(
    suite_name: str,
    reason: str,
    source_type: str,
    c: int,
    *,
    timeout_seconds: float = 300.0,
    max_width_search_vars: int = 28,
    strict_unsat_external: bool = True,
    drat_trim_path: str | Path | None = None,
    message: str = "",
) -> dict[str, Any]:
    summary = summarize_public_results([])
    return {
        "version": "0.9.1",
        "benchmark_kind": "public",
        "suite_name": suite_name,
        "suite_source_type": source_type,
        "suite_status": SUITE_NOT_RUN,
        "not_run_reason": reason,
        "not_run_message": message,
        "c_parameter": c,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "timeout_seconds": timeout_seconds,
        "max_width_search_vars": max_width_search_vars,
        "strict_unsat_external": strict_unsat_external,
        "drat_trim_path": str(drat_trim_path) if drat_trim_path is not None else "",
        "strict_unsat_external_pass": True,
        "strict_unsat_external_failures": [],
        "cases": [],
        "per_case_results": [],
        "summary": summary,
    }


def public_suite_cases(name: str, *, max_instances: int | None = None) -> list[PublicBenchmarkCase]:
    if name == "cnfgen-small":
        cases = cnfgen_small_cases()
    elif name == "demo-cnfgen-artifact":
        cases = demo_cnfgen_artifact_cases()
    else:
        raise ValueError("supported public suites: cnfgen-small, demo-cnfgen-artifact")
    return cases[:max_instances] if max_instances is not None else cases


def _post_s_formula(formula: CNFFormula) -> CNFFormula:
    from .certificate import StepLogger

    logger = StepLogger()
    simplified, _status = simplify(formula, logger, log_component_decomposition=False)
    return simplified


def _category_for_result(
    status: str,
    original_verification: bool,
    drat_status: dict[str, Any] | None,
) -> str:
    if status == SAT:
        return SAT_ASSIGNMENT_VERIFIED if original_verification else ERROR
    if status == NO_COLLAPSE:
        return NO_COLLAPSE_FOUND
    if status == XOR_UNSAT_NATIVE:
        if (
            drat_status is not None
            and drat_status.get("drat_export_status") == "EXPORTED"
            and drat_status.get("external_checker") == "DRAT_TRIM"
            and drat_status.get("external_checker_ran") is True
            and drat_status.get("external_checker_verified") is True
            and drat_status.get("proof_base") == "original_cnf"
        ):
            return UNSAT_DRAT_EXPORTED_VERIFIED
        return UNSAT_XOR_NATIVE_ONLY
    if status != UNSAT:
        return ERROR
    if drat_status is None:
        return UNSAT_NOT_EXTERNALLY_VERIFIED
    if drat_status.get("drat_export_status") == "UNSUPPORTED":
        return UNSUPPORTED_DRAT
    if (
        drat_status.get("drat_export_status") == "EXPORTED"
        and drat_status.get("external_checker") == "DRAT_TRIM"
        and drat_status.get("external_checker_ran") is True
        and drat_status.get("external_checker_verified") is True
    ):
        return UNSAT_DRAT_EXPORTED_VERIFIED
    return UNSAT_NOT_EXTERNALLY_VERIFIED


def _xor_discovery_route_from_status(drat_status: dict[str, Any] | None) -> str:
    if drat_status and drat_status.get("source") == "detected_cnf_pattern":
        return DISCOVERY_XOR_NATIVE
    return DISCOVERY_XOR_SIDECAR


def _public_metadata_for_result(
    status: str,
    original_verification: bool,
    drat_status: dict[str, Any] | None,
    *,
    discovery_route: str = "",
) -> dict[str, Any]:
    category = _category_for_result(status, original_verification, drat_status)
    logical_status = "UNSAT" if status in {UNSAT, XOR_UNSAT_NATIVE} else NO_COLLAPSE_FOUND if status == NO_COLLAPSE else status
    external_verified = category == UNSAT_DRAT_EXPORTED_VERIFIED
    if status == SAT and category == SAT_ASSIGNMENT_VERIFIED:
        certification = CERTIFICATION_SAT_ASSIGNMENT
    elif external_verified:
        certification = CERTIFICATION_EXTERNAL_DRAT
    elif category == UNSAT_XOR_NATIVE_ONLY:
        certification = CERTIFICATION_NATIVE_XOR
    else:
        certification = CERTIFICATION_NOT_EXTERNAL
    route = discovery_route
    if status == XOR_UNSAT_NATIVE:
        route = _xor_discovery_route_from_status(drat_status)
    return {
        "status": logical_status,
        "internal_status": status,
        "discovery_route": route,
        "certification_level": certification,
        "public_category": category,
        "external_drat": external_verified,
        "drat_claim": "EXPORTED_VERIFIED" if external_verified else str((drat_status or {}).get("drat_claim", "NOT_EXPORTED")),
        "proof_base": "original_cnf" if external_verified else (drat_status or {}).get("proof_base"),
    }


def _extract_drat_trim_seconds(drat_status: dict[str, Any] | None) -> float | None:
    if not drat_status:
        return None
    text = str(drat_status.get("external_checker_stdout_excerpt", ""))
    match = _DRAT_TRIM_TIME_PATTERN.search(text)
    if not match:
        return None
    return round(float(match.group(1)), 6)


def _public_case_worker(
    payload: dict[str, Any],
    c: int,
    max_width_search_vars: int,
    export_certs_dir: str | None,
    drat_trim_path: str | None,
    queue: multiprocessing.Queue,
) -> None:
    started = time.perf_counter()
    try:
        formula = parse_dimacs(payload["dimacs_text"])
        original = structural_metrics(formula)
        post_s = _post_s_formula(formula)
        post = structural_metrics(post_s)
        width_found, width_status, width_skip_reason = width_order_measurement(
            post_s,
            c,
            max_width_search_vars=max_width_search_vars,
        )

        solver_start = time.perf_counter()
        path = solve(formula, c)
        solver_seconds = time.perf_counter() - solver_start

        wcert_path = ""
        proof_path = ""
        drat_status: dict[str, Any] | None = None
        drat_export_seconds = 0.0
        if export_certs_dir is not None:
            safe_name = payload["instance_name"].replace("/", "_").replace("\\", "_")
            cert_path = Path(export_certs_dir) / f"{safe_name}.wcert"
            export_start = time.perf_counter()
            export_certificate_bundle(
                formula,
                path,
                cert_path,
                original_dimacs_text=payload["dimacs_text"],
                export_drat=path.status == UNSAT,
                drat_trim_path=drat_trim_path,
            )
            drat_export_seconds = time.perf_counter() - export_start
            wcert_path = str(cert_path)
            status_path = cert_path / "drat_status.json"
            if status_path.exists():
                drat_status = json.loads(status_path.read_text(encoding="utf-8"))
            proof_file = cert_path / "proof.drat"
            if proof_file.exists():
                proof_path = str(proof_file)

        public_metadata = _public_metadata_for_result(
            path.status,
            path.original_verification,
            drat_status,
            discovery_route=path.discovery_route,
        )
        category = public_metadata["public_category"]
        strict_pass = category not in {UNSAT_NOT_EXTERNALLY_VERIFIED, UNSUPPORTED_DRAT, UNSAT_XOR_NATIVE_ONLY}
        result = {
            "instance_name": payload["instance_name"],
            "source_suite": payload["source_suite"],
            "family": payload["family"],
            **public_metadata,
            "final_class": path.final_class,
            "c_parameter": c,
            "original_formula_hash": formula.formula_hash,
            "original_num_vars": original["num_vars"],
            "original_num_clauses": original["num_clauses"],
            "post_s_num_vars": post["num_vars"],
            "post_s_num_clauses": post["num_clauses"],
            "original_max_clause_width": original["max_clause_width"],
            "post_s_max_clause_width": post["max_clause_width"],
            "original_clique_lower_bound": original["clique_lower_bound"],
            "post_s_width_order_found": width_found,
            "post_s_width_order_status": width_status,
            "post_s_width_order_skip_reason": width_skip_reason,
            "collapse_path_length": len(path.steps),
            "num_bce_removed": sum(len(step.removed_clauses) for step in path.steps if step.type == "BCE"),
            "num_ple_assignments": sum(len(step.assigned_literals) for step in path.steps if step.type == "PLE"),
            "num_up_assignments": sum(len(step.assigned_literals) for step in path.steps if step.type == "UP"),
            "num_subsumed_clauses": sum(len(step.removed_clauses) for step in path.steps if step.type == "SUB"),
            "num_vars_eliminated": sum(1 for step in path.steps if step.type == "VE"),
            "solver_time_seconds": round(solver_seconds, 6),
            "drat_export_time_seconds": round(drat_export_seconds, 6),
            "drat_trim_time_seconds": _extract_drat_trim_seconds(drat_status),
            "total_time_seconds": round(time.perf_counter() - started, 6),
            "certificate_hash": path.certificate_hash,
            "wcert_path": wcert_path,
            "proof_drat_path": proof_path,
            "drat_export_status": (drat_status or {}).get("drat_export_status", ""),
            "external_checker": (drat_status or {}).get("external_checker", ""),
            "external_checker_ran": bool((drat_status or {}).get("external_checker_ran", False)),
            "external_checker_verified": bool((drat_status or {}).get("external_checker_verified", False)),
            "strict_unsat_external_pass": strict_pass,
            "error_message": "",
            "solved_route": path.final_class if path.status == SAT else path.status,
            "failure_reason": "no collapse found under current grammar and c" if path.status == NO_COLLAPSE else "",
            "clause_reduction_pct": round(
                ((original["num_clauses"] - post["num_clauses"]) / original["num_clauses"] * 100.0)
                if original["num_clauses"]
                else 0.0,
                3,
            ),
            "variable_reduction_pct": round(
                ((original["num_vars"] - post["num_vars"]) / original["num_vars"] * 100.0)
                if original["num_vars"]
                else 0.0,
                3,
            ),
        }
        queue.put(result)
    except Exception as exc:  # pragma: no cover - defensive benchmark isolation
        queue.put(
            {
                "instance_name": payload.get("instance_name", ""),
                "source_suite": payload.get("source_suite", ""),
                "family": payload.get("family", ""),
                "public_category": ERROR,
                "status": ERROR,
                "internal_status": ERROR,
                "discovery_route": "ERROR",
                "certification_level": CERTIFICATION_NOT_EXTERNAL,
                "final_class": ERROR,
                "c_parameter": c,
                "total_time_seconds": round(time.perf_counter() - started, 6),
                "strict_unsat_external_pass": False,
                "external_drat": False,
                "drat_claim": "NOT_EXPORTED",
                "proof_base": None,
                "error_message": f"{exc}\n{traceback.format_exc()}",
            }
        )


def _timeout_result(case: PublicBenchmarkCase, c: int, timeout_seconds: float) -> dict[str, Any]:
    return {
        "instance_name": case.instance_name,
        "source_suite": case.source_suite,
        "family": case.family,
        "public_category": TIMEOUT,
        "status": TIMEOUT,
        "internal_status": TIMEOUT,
        "discovery_route": "TIMEOUT",
        "certification_level": CERTIFICATION_NOT_EXTERNAL,
        "final_class": TIMEOUT,
        "c_parameter": c,
        "timeout_seconds": timeout_seconds,
        "timeout_stage": "benchmark_instance",
        "total_time_seconds": timeout_seconds,
        "strict_unsat_external_pass": True,
        "external_drat": False,
        "drat_claim": "NOT_EXPORTED",
        "proof_base": None,
        "error_message": "",
    }


def run_public_case(
    case: PublicBenchmarkCase,
    c: int,
    *,
    timeout_seconds: float = 300.0,
    max_width_search_vars: int = 28,
    export_certs_dir: str | Path | None = None,
    drat_trim_path: str | Path | None = None,
) -> dict[str, Any]:
    if timeout_seconds <= 0:
        return _timeout_result(case, c, timeout_seconds)

    if export_certs_dir is not None:
        Path(export_certs_dir).mkdir(parents=True, exist_ok=True)

    ctx = multiprocessing.get_context("spawn")
    queue: multiprocessing.Queue = ctx.Queue()
    process = ctx.Process(
        target=_public_case_worker,
        args=(
            case.to_payload(),
            c,
            max_width_search_vars,
            str(export_certs_dir) if export_certs_dir is not None else None,
            str(drat_trim_path) if drat_trim_path is not None else None,
            queue,
        ),
    )
    process.start()
    process.join(timeout_seconds)
    if process.is_alive():
        process.terminate()
        process.join(5)
        return _timeout_result(case, c, timeout_seconds)
    if not queue.empty():
        return dict(queue.get())
    return {
        "instance_name": case.instance_name,
        "source_suite": case.source_suite,
        "family": case.family,
        "public_category": ERROR,
        "status": ERROR,
        "internal_status": ERROR,
        "discovery_route": "ERROR",
        "certification_level": CERTIFICATION_NOT_EXTERNAL,
        "final_class": ERROR,
        "c_parameter": c,
        "strict_unsat_external_pass": False,
        "external_drat": False,
        "drat_claim": "NOT_EXPORTED",
        "proof_base": None,
        "error_message": f"worker exited without result, exit_code={process.exitcode}",
    }


def _category_counts(results: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts = {category: 0 for category in PUBLIC_CATEGORIES}
    for result in results:
        category = str(result.get("public_category", ERROR))
        counts[category] = counts.get(category, 0) + 1
    return counts


def summarize_public_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    unsat = [r for r in results if r.get("status") == UNSAT]
    return {
        "total_cases": total,
        "category_counts": _category_counts(results),
        "strict_unsat_external_pass": all(r.get("strict_unsat_external_pass", False) for r in results),
        "strict_unsat_external_failures": [
            r.get("instance_name", "")
            for r in results
            if r.get("public_category") in {UNSAT_NOT_EXTERNALLY_VERIFIED, UNSUPPORTED_DRAT, UNSAT_XOR_NATIVE_ONLY}
        ],
        "unsat_total": len(unsat),
        "externally_verified_unsat_count": sum(
            1 for r in results if r.get("public_category") == UNSAT_DRAT_EXPORTED_VERIFIED
        ),
        "unverified_unsat_count": sum(
            1 for r in results if r.get("public_category") == UNSAT_NOT_EXTERNALLY_VERIFIED
        ),
        "unsupported_drat_count": sum(1 for r in results if r.get("public_category") == UNSUPPORTED_DRAT),
        "xor_native_unsat_count": sum(1 for r in results if r.get("public_category") == UNSAT_XOR_NATIVE_ONLY),
        "timeout_count": sum(1 for r in results if r.get("public_category") == TIMEOUT),
        "error_count": sum(1 for r in results if r.get("public_category") == ERROR),
        "average_collapse_path_length": round(
            sum(float(r.get("collapse_path_length", 0) or 0) for r in results) / total,
            3,
        )
        if total
        else 0.0,
        "average_clause_reduction_pct": round(
            sum(float(r.get("clause_reduction_pct", 0) or 0) for r in results) / total,
            3,
        )
        if total
        else 0.0,
        "average_variable_reduction_pct": round(
            sum(float(r.get("variable_reduction_pct", 0) or 0) for r in results) / total,
            3,
        )
        if total
        else 0.0,
    }


def run_public_benchmark(
    cases: Iterable[PublicBenchmarkCase],
    c: int,
    *,
    timeout_seconds: float = 300.0,
    max_width_search_vars: int = 28,
    strict_unsat_external: bool = False,
    drat_trim_path: str | Path | None = None,
    export_certs_dir: str | Path | None = None,
    timestamp: str | None = None,
    suite_name: str = "public",
    suite_source_type: str = "",
    suite_status: str = SUITE_RUN,
    not_run_reason: str | None = None,
) -> dict[str, Any]:
    case_list = list(cases)
    cert_root = Path(export_certs_dir) if export_certs_dir is not None else None
    if cert_root is None:
        cert_root = Path(tempfile.mkdtemp(prefix="witnora-public-certs-"))
    cert_root.mkdir(parents=True, exist_ok=True)
    results = [
        run_public_case(
            case,
            c,
            timeout_seconds=timeout_seconds,
            max_width_search_vars=max_width_search_vars,
            export_certs_dir=cert_root,
            drat_trim_path=drat_trim_path,
        )
        for case in case_list
    ]
    summary = summarize_public_results(results)
    data = {
        "version": "0.9.1",
        "benchmark_kind": "public",
        "suite_name": suite_name,
        "suite_source_type": suite_source_type,
        "suite_status": suite_status,
        "not_run_reason": not_run_reason,
        "c_parameter": c,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        "timeout_seconds": timeout_seconds,
        "max_width_search_vars": max_width_search_vars,
        "strict_unsat_external": strict_unsat_external,
        "drat_trim_path": str(drat_trim_path) if drat_trim_path is not None else "",
        "strict_unsat_external_pass": bool(summary["strict_unsat_external_pass"]),
        "strict_unsat_external_failures": summary["strict_unsat_external_failures"],
        "cases": [case.to_dict() for case in case_list],
        "per_case_results": results,
        "summary": summary,
    }
    return data


def write_public_csv(data: dict[str, Any], path: str | Path) -> None:
    rows = data.get("per_case_results", [])
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PUBLIC_CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return lines


def generate_public_markdown_report(data: dict[str, Any]) -> str:
    results = list(data.get("per_case_results", []))
    summary = dict(data.get("summary", {}))
    category_counts = summary.get("category_counts", {})
    route_counts: dict[str, int] = {}
    for result in results:
        route = str(result.get("final_class", ""))
        route_counts[route] = route_counts.get(route, 0) + 1

    lines = ["# Witnora Public Benchmark Report", ""]
    lines.append("## Benchmark Source Description")
    suites = sorted({str(result.get("source_suite", "")) for result in results})
    lines.append("Suites: " + (", ".join(suites) if suites else str(data.get("suite_name", ""))))
    lines.append(f"Suite source type: {data.get('suite_source_type', '')}")
    lines.append(f"Suite status: {data.get('suite_status', SUITE_RUN)}")
    if data.get("suite_status") == SUITE_NOT_RUN:
        lines.append(f"NOT_RUN reason: {data.get('not_run_reason', '')}")
        if data.get("not_run_message"):
            lines.append(str(data.get("not_run_message")))
    lines.append("")
    lines.append("## Configuration")
    lines.extend(
        _table(
            ["Field", "Value"],
            [
                ["c", data.get("c_parameter", "")],
                ["timeout_seconds", data.get("timeout_seconds", "")],
                ["max_width_search_vars", data.get("max_width_search_vars", "")],
                ["drat_trim_path", data.get("drat_trim_path", "")],
                ["strict_unsat_external", data.get("strict_unsat_external", "")],
                ["strict_unsat_external_pass", data.get("strict_unsat_external_pass", "")],
            ],
        )
    )
    lines.append("")
    lines.append("## Category Counts")
    lines.extend(_table(["Category", "Count"], [[c, category_counts.get(c, 0)] for c in PUBLIC_CATEGORIES]))
    lines.append("")
    lines.append("## DRAT Verification Summary")
    lines.extend(
        _table(
            ["Metric", "Value"],
            [
                ["UNSAT total", summary.get("unsat_total", 0)],
                ["externally verified UNSAT", summary.get("externally_verified_unsat_count", 0)],
                ["unverified UNSAT", summary.get("unverified_unsat_count", 0)],
                ["unsupported DRAT", summary.get("unsupported_drat_count", 0)],
                ["drat-trim failures", len(summary.get("strict_unsat_external_failures", []))],
            ],
        )
    )
    lines.append("")
    lines.append("## Collapse Route Summary")
    lines.extend(_table(["Final Class", "Count"], sorted(route_counts.items())))
    lines.append("")
    lines.append("## Reduction Statistics")
    lines.extend(
        _table(
            ["Metric", "Value"],
            [
                ["average_clause_reduction_pct", summary.get("average_clause_reduction_pct", 0)],
                ["average_variable_reduction_pct", summary.get("average_variable_reduction_pct", 0)],
                ["average_collapse_path_length", summary.get("average_collapse_path_length", 0)],
            ],
        )
    )
    lines.append("")
    lines.append("## No-Collapse Analysis")
    no_collapse = [r for r in results if r.get("public_category") == NO_COLLAPSE_FOUND]
    lines.append(f"No-collapse count: {len(no_collapse)}")
    skipped = [r for r in results if r.get("post_s_width_order_status") == WIDTH_SKIPPED_SIZE_CAP]
    lines.append(f"Width search skipped count: {len(skipped)}")
    lines.append("")
    lines.append("## Timeout Analysis")
    timeouts = [r for r in results if r.get("public_category") == TIMEOUT]
    lines.append(f"Timeout count: {len(timeouts)}")
    lines.append("")
    lines.append("## Claims Allowed / Claims Forbidden")
    lines.append("Allowed: public benchmark categories separate SAT assignment verification, real drat-trim verified UNSAT, unverified UNSAT, unsupported DRAT, no-collapse, timeout, and errors.")
    lines.append("Forbidden: no P vs NP claim, no HARD/UNKNOWN status, no general SAT solver claim, no full DRAT/RAT/LRAT/FRAT claim, and no UNSAT counted as certified without real drat-trim verification.")
    lines.append("")
    return "\n".join(lines)
