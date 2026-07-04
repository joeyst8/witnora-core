"""Benchmark and collapse-measurement layer for Witnora-Core."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
from typing import Any, Iterable

from .certificate import NO_COLLAPSE, SAT, UNSAT, StepLogger
from .cnf import CNFFormula
from .dimacs import load_dimacs
from .families import (
    bce_heavy_family,
    blocked_clique_collapse_family,
    bounded_treewidth_chain_family,
    component_mixed_family,
    random_2sat_family,
    random_3sat_family,
    tautology_noise_family,
    unsat_unit_conflict_family,
)
from .primal import graph_edges, primal_graph
from .proof import export_certificate_bundle
from .runner import solve
from .simplify import simplify
from .treewidth import find_elimination_order

VERSION = "0.9.0"

WIDTH_FOUND = "FOUND"
WIDTH_NOT_FOUND = "NOT_FOUND"
WIDTH_SKIPPED_SIZE_CAP = "SKIPPED_SIZE_CAP"
UNSAT_DRAT_EXPORTED_VERIFIED = "UNSAT_DRAT_EXPORTED_VERIFIED"
UNSAT_NOT_EXTERNALLY_VERIFIED = "UNSAT_NOT_EXTERNALLY_VERIFIED"

CSV_COLUMNS = [
    "case_name",
    "family",
    "status",
    "final_class",
    "solved_route",
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
    "original_verification",
    "time_ms",
    "certificate_hash",
]


@dataclass(frozen=True)
class BenchmarkCase:
    name: str
    family: str
    formula: CNFFormula
    source: str
    notes: str = ""
    original_dimacs_text: str | None = None

    @property
    def n_vars(self) -> int:
        return self.formula.num_vars

    @property
    def n_clauses(self) -> int:
        return self.formula.num_clauses

    @property
    def formula_hash(self) -> str:
        return self.formula.formula_hash

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "family": self.family,
            "n_vars": self.n_vars,
            "n_clauses": self.n_clauses,
            "formula_hash": self.formula_hash,
            "source": self.source,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class BenchmarkResult:
    case_name: str
    family: str
    status: str
    final_class: str
    c_parameter: int
    original_formula_hash: str
    certificate_hash: str
    original_num_vars: int
    original_num_clauses: int
    post_s_num_vars: int
    post_s_num_clauses: int
    original_max_clause_width: int
    post_s_max_clause_width: int
    original_primal_edges: int
    post_s_primal_edges: int
    original_clique_lower_bound: int
    post_s_width_order_found: bool | None
    post_s_width_order_status: str
    post_s_width_order_skip_reason: str | None
    solved_route: str
    collapse_path_length: int
    num_bce_removed: int
    num_ple_assignments: int
    num_up_assignments: int
    num_subsumed_clauses: int
    num_vars_eliminated: int
    original_verification: bool
    time_ms: float
    failure_reason: str
    determinism_pass: bool | None = None
    certificate_bundle_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_name": self.case_name,
            "family": self.family,
            "status": self.status,
            "final_class": self.final_class,
            "c_parameter": self.c_parameter,
            "original_formula_hash": self.original_formula_hash,
            "certificate_hash": self.certificate_hash,
            "original_num_vars": self.original_num_vars,
            "original_num_clauses": self.original_num_clauses,
            "post_s_num_vars": self.post_s_num_vars,
            "post_s_num_clauses": self.post_s_num_clauses,
            "original_max_clause_width": self.original_max_clause_width,
            "post_s_max_clause_width": self.post_s_max_clause_width,
            "original_primal_edges": self.original_primal_edges,
            "post_s_primal_edges": self.post_s_primal_edges,
            "original_clique_lower_bound": self.original_clique_lower_bound,
            "post_s_width_order_found": self.post_s_width_order_found,
            "post_s_width_order_status": self.post_s_width_order_status,
            "post_s_width_order_skip_reason": self.post_s_width_order_skip_reason,
            "solved_route": self.solved_route,
            "collapse_path_length": self.collapse_path_length,
            "num_bce_removed": self.num_bce_removed,
            "num_ple_assignments": self.num_ple_assignments,
            "num_up_assignments": self.num_up_assignments,
            "num_subsumed_clauses": self.num_subsumed_clauses,
            "num_vars_eliminated": self.num_vars_eliminated,
            "original_verification": self.original_verification,
            "time_ms": self.time_ms,
            "failure_reason": self.failure_reason,
            "determinism_pass": self.determinism_pass,
            "certificate_bundle_path": self.certificate_bundle_path,
        }


@dataclass(frozen=True)
class BenchmarkSummary:
    total_cases: int
    solved_count: int
    sat_count: int
    unsat_count: int
    no_collapse_count: int
    solved_by_empty: int
    solved_by_2sat: int
    solved_by_treewidth: int
    solved_by_components: int
    average_collapse_path_length: float
    average_clause_reduction_pct: float
    average_variable_reduction_pct: float
    certificate_hash_determinism_pass_rate: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_cases": self.total_cases,
            "solved_count": self.solved_count,
            "sat_count": self.sat_count,
            "unsat_count": self.unsat_count,
            "no_collapse_count": self.no_collapse_count,
            "solved_by_empty": self.solved_by_empty,
            "solved_by_2sat": self.solved_by_2sat,
            "solved_by_treewidth": self.solved_by_treewidth,
            "solved_by_components": self.solved_by_components,
            "average_collapse_path_length": self.average_collapse_path_length,
            "average_clause_reduction_pct": self.average_clause_reduction_pct,
            "average_variable_reduction_pct": self.average_variable_reduction_pct,
            "certificate_hash_determinism_pass_rate": self.certificate_hash_determinism_pass_rate,
        }


def max_clause_width(formula: CNFFormula) -> int:
    return max((len(clause) for clause in formula.clauses), default=0)


def structural_metrics(formula: CNFFormula) -> dict[str, int]:
    width = max_clause_width(formula)
    graph = primal_graph(formula)
    return {
        "num_vars": formula.num_vars,
        "num_clauses": formula.num_clauses,
        "max_clause_width": width,
        "primal_edges": len(graph_edges(graph)),
        "clique_lower_bound": max(0, width - 1),
    }


def post_s_formula(formula: CNFFormula) -> CNFFormula:
    logger = StepLogger()
    simplified, _status = simplify(
        formula,
        logger,
        log_component_decomposition=False,
    )
    return simplified


def width_order_found_for_c(
    formula: CNFFormula,
    c: int,
    *,
    max_width_search_vars: int = 28,
) -> bool | None:
    graph = primal_graph(formula)
    if len(graph) > max_width_search_vars:
        return None
    return find_elimination_order(graph, c) is not None


def width_order_measurement(
    formula: CNFFormula,
    c: int,
    *,
    max_width_search_vars: int = 28,
) -> tuple[bool | None, str, str | None]:
    graph = primal_graph(formula)
    if len(graph) > max_width_search_vars:
        return (
            None,
            WIDTH_SKIPPED_SIZE_CAP,
            "num_vars_exceeds_max_width_search_vars",
        )
    found = find_elimination_order(graph, c) is not None
    return found, WIDTH_FOUND if found else WIDTH_NOT_FOUND, None


def solved_route(status: str, final_class: str) -> str:
    if status == NO_COLLAPSE:
        return "NO_COLLAPSE"
    if status == UNSAT:
        return "UNSAT"
    if final_class in {"EMPTY", "2SAT", "TREEWIDTH_LEQ_C", "COMPONENTS_SOLVED"}:
        return final_class
    return final_class


def failure_reason(status: str) -> str:
    if status == NO_COLLAPSE:
        return "no collapse found under current grammar and c"
    if status not in {SAT, UNSAT}:
        return status
    return ""


def unsat_external_verification_category(
    status: str,
    drat_status: dict[str, Any] | None,
) -> str | None:
    """Classify whether an UNSAT benchmark result has external DRAT verification."""

    if status != UNSAT:
        return None
    if (
        drat_status is not None
        and drat_status.get("drat_export_status") == "EXPORTED"
        and drat_status.get("external_checker") == "DRAT_TRIM"
        and drat_status.get("external_checker_ran") is True
        and drat_status.get("external_checker_verified") is True
    ):
        return UNSAT_DRAT_EXPORTED_VERIFIED
    return UNSAT_NOT_EXTERNALLY_VERIFIED


def enforce_unsat_external_verification(
    status: str,
    drat_status: dict[str, Any] | None,
    *,
    strict: bool = False,
) -> str | None:
    """Guard for future benchmark modes requiring externally checked UNSAT."""

    category = unsat_external_verification_category(status, drat_status)
    if strict and category == UNSAT_NOT_EXTERNALLY_VERIFIED:
        raise ValueError("UNSAT result lacks external drat-trim verification")
    return category


def compare_deterministic_run(first: Any, second: Any) -> bool:
    first_dict = first.to_dict()
    second_dict = second.to_dict()
    return (
        first.certificate_hash == second.certificate_hash
        and first.status == second.status
        and first_dict["collapse_path"] == second_dict["collapse_path"]
        and first_dict["component_results"] == second_dict["component_results"]
    )


def run_case(
    case: BenchmarkCase,
    c: int,
    *,
    determinism_check: bool = False,
    max_width_search_vars: int = 28,
    export_cert_path: str | Path | None = None,
) -> BenchmarkResult:
    original = structural_metrics(case.formula)
    post_s = post_s_formula(case.formula)
    post = structural_metrics(post_s)
    path = solve(case.formula, c)
    width_found, width_status, width_skip_reason = width_order_measurement(
        post_s,
        c,
        max_width_search_vars=max_width_search_vars,
    )

    determinism_pass: bool | None = None
    if determinism_check:
        second = solve(case.formula, c)
        determinism_pass = compare_deterministic_run(path, second)

    certificate_bundle_path: str | None = None
    if export_cert_path is not None:
        export_certificate_bundle(
            case.formula,
            path,
            export_cert_path,
            original_dimacs_text=case.original_dimacs_text or case.formula.canonical_dimacs(),
        )
        certificate_bundle_path = str(export_cert_path)

    return BenchmarkResult(
        case_name=case.name,
        family=case.family,
        status=path.status,
        final_class=path.final_class,
        c_parameter=c,
        original_formula_hash=case.formula.formula_hash,
        certificate_hash=path.certificate_hash,
        original_num_vars=original["num_vars"],
        original_num_clauses=original["num_clauses"],
        post_s_num_vars=post["num_vars"],
        post_s_num_clauses=post["num_clauses"],
        original_max_clause_width=original["max_clause_width"],
        post_s_max_clause_width=post["max_clause_width"],
        original_primal_edges=original["primal_edges"],
        post_s_primal_edges=post["primal_edges"],
        original_clique_lower_bound=original["clique_lower_bound"],
        post_s_width_order_found=width_found,
        post_s_width_order_status=width_status,
        post_s_width_order_skip_reason=width_skip_reason,
        solved_route=solved_route(path.status, path.final_class),
        collapse_path_length=len(path.steps),
        num_bce_removed=sum(len(step.removed_clauses) for step in path.steps if step.type == "BCE"),
        num_ple_assignments=sum(len(step.assigned_literals) for step in path.steps if step.type == "PLE"),
        num_up_assignments=sum(len(step.assigned_literals) for step in path.steps if step.type == "UP"),
        num_subsumed_clauses=sum(len(step.removed_clauses) for step in path.steps if step.type == "SUB"),
        num_vars_eliminated=sum(1 for step in path.steps if step.type == "VE"),
        original_verification=path.original_verification,
        time_ms=float(path.stats.get("time_ms", 0.0)),
        failure_reason=failure_reason(path.status),
        determinism_pass=determinism_pass,
        certificate_bundle_path=certificate_bundle_path,
    )


def clause_reduction_pct(result: BenchmarkResult) -> float:
    if result.original_num_clauses == 0:
        return 0.0
    removed = result.original_num_clauses - result.post_s_num_clauses
    return (removed / result.original_num_clauses) * 100.0


def variable_reduction_pct(result: BenchmarkResult) -> float:
    if result.original_num_vars == 0:
        return 0.0
    removed = result.original_num_vars - result.post_s_num_vars
    return (removed / result.original_num_vars) * 100.0


def summarize_results(results: Iterable[BenchmarkResult]) -> BenchmarkSummary:
    items = list(results)
    total = len(items)
    solved = sum(1 for item in items if item.status in {SAT, UNSAT})
    checked = [item for item in items if item.determinism_pass is not None]
    pass_rate = None
    if checked:
        pass_rate = sum(1 for item in checked if item.determinism_pass) / len(checked)
    return BenchmarkSummary(
        total_cases=total,
        solved_count=solved,
        sat_count=sum(1 for item in items if item.status == SAT),
        unsat_count=sum(1 for item in items if item.status == UNSAT),
        no_collapse_count=sum(1 for item in items if item.status == NO_COLLAPSE),
        solved_by_empty=sum(1 for item in items if item.solved_route == "EMPTY"),
        solved_by_2sat=sum(1 for item in items if item.solved_route == "2SAT"),
        solved_by_treewidth=sum(1 for item in items if item.solved_route == "TREEWIDTH_LEQ_C"),
        solved_by_components=sum(1 for item in items if item.solved_route == "COMPONENTS_SOLVED"),
        average_collapse_path_length=round(
            sum(item.collapse_path_length for item in items) / total,
            3,
        )
        if total
        else 0.0,
        average_clause_reduction_pct=round(
            sum(clause_reduction_pct(item) for item in items) / total,
            3,
        )
        if total
        else 0.0,
        average_variable_reduction_pct=round(
            sum(variable_reduction_pct(item) for item in items) / total,
            3,
        )
        if total
        else 0.0,
        certificate_hash_determinism_pass_rate=pass_rate,
    )


def synthetic_cases(scale: str = "small") -> list[BenchmarkCase]:
    if scale not in {"small", "medium"}:
        raise ValueError("scale must be 'small' or 'medium'")

    small = [
        BenchmarkCase(
            "blocked_clique_n6",
            "blocked_clique_collapse",
            blocked_clique_collapse_family(6),
            "synthetic",
            "unbounded original clique lower bound, BCE collapse",
        ),
        BenchmarkCase(
            "random_2sat_seed7",
            "random_2sat",
            random_2sat_family(8, 16, seed=7),
            "synthetic",
            "deterministic random 2-CNF",
        ),
        BenchmarkCase(
            "random_3sat_seed13",
            "random_3sat",
            random_3sat_family(8, 24, seed=13),
            "synthetic",
            "deterministic random 3-CNF no-collapse probe",
        ),
        BenchmarkCase(
            "bounded_treewidth_chain_n5",
            "bounded_treewidth_chain",
            bounded_treewidth_chain_family(5),
            "synthetic",
            "non-2-CNF width-2 core",
        ),
        BenchmarkCase(
            "bce_heavy_4x3",
            "bce_heavy",
            bce_heavy_family(4, 3),
            "synthetic",
            "three independent blocked-clique components",
        ),
        BenchmarkCase(
            "component_mixed_n3",
            "component_mixed",
            component_mixed_family(3),
            "synthetic",
            "independent BCE, 2-SAT, and bounded-treewidth components",
        ),
        BenchmarkCase(
            "unsat_unit_conflict",
            "unsat_unit_conflict",
            unsat_unit_conflict_family(),
            "synthetic",
            "minimal UP contradiction",
        ),
        BenchmarkCase(
            "tautology_noise_n6",
            "tautology_noise",
            tautology_noise_family(6),
            "synthetic",
            "tautological clauses removed during normalization",
        ),
    ]
    if scale == "small":
        return small

    cases: list[BenchmarkCase] = []
    for n in [5, 10, 20, 30]:
        cases.append(
            BenchmarkCase(
                f"blocked_clique_n{n}",
                "blocked_clique_collapse",
                blocked_clique_collapse_family(n),
                "synthetic",
                "BCE strictness family",
            )
        )
    for n_vars, n_clauses, seed in [(10, 20, 1), (20, 40, 2), (30, 60, 3)]:
        cases.append(
            BenchmarkCase(
                f"random_2sat_v{n_vars}_c{n_clauses}_s{seed}",
                "random_2sat",
                random_2sat_family(n_vars, n_clauses, seed),
                "synthetic",
                "deterministic random 2-CNF",
            )
        )
    for n_vars, n_clauses, seed in [(10, 30, 11), (16, 64, 13), (24, 96, 17)]:
        cases.append(
            BenchmarkCase(
                f"random_3sat_v{n_vars}_c{n_clauses}_s{seed}",
                "random_3sat",
                random_3sat_family(n_vars, n_clauses, seed),
                "synthetic",
                "deterministic random 3-CNF no-collapse probe",
            )
        )
    for n in [5, 7, 9]:
        cases.append(
            BenchmarkCase(
                f"bounded_treewidth_chain_n{n}",
                "bounded_treewidth_chain",
                bounded_treewidth_chain_family(n),
                "synthetic",
                "non-2-CNF bounded-width chain",
            )
        )
    for width, count in [(4, 2), (6, 3), (8, 4)]:
        cases.append(
            BenchmarkCase(
                f"bce_heavy_w{width}_k{count}",
                "bce_heavy",
                bce_heavy_family(width, count),
                "synthetic",
                "multiple blocked-clique components",
            )
        )
    for n in [3, 5, 8]:
        cases.append(
            BenchmarkCase(
                f"component_mixed_n{n}",
                "component_mixed",
                component_mixed_family(n),
                "synthetic",
                "independent BCE, 2-SAT, and bounded-treewidth components",
            )
        )
    cases.extend(
        [
            BenchmarkCase(
                "unsat_unit_conflict",
                "unsat_unit_conflict",
                unsat_unit_conflict_family(),
                "synthetic",
                "minimal UP contradiction",
            ),
            BenchmarkCase(
                "tautology_noise_n12",
                "tautology_noise",
                tautology_noise_family(12),
                "synthetic",
                "tautological clauses removed during normalization",
            ),
        ]
    )
    return cases


def dimacs_cases(dimacs_dir: str | Path) -> list[BenchmarkCase]:
    root = Path(dimacs_dir)
    paths = sorted(
        path
        for path in root.iterdir()
        if path.is_file() and path.suffix.lower() in {".cnf", ".dimacs"}
    )
    cases: list[BenchmarkCase] = []
    for path in paths:
        formula = load_dimacs(path)
        cases.append(
            BenchmarkCase(
                name=path.stem,
                family="dimacs",
                formula=formula,
                source=str(path),
                notes="user-provided DIMACS",
                original_dimacs_text=path.read_text(encoding="utf-8"),
            )
        )
    return cases


def run_benchmark(
    cases: Iterable[BenchmarkCase],
    c: int,
    *,
    determinism_check: bool = False,
    max_width_search_vars: int = 28,
    timestamp: str | None = None,
    scale: str | None = None,
    export_certs_dir: str | Path | None = None,
) -> dict[str, Any]:
    case_list = list(cases)
    cert_root = Path(export_certs_dir) if export_certs_dir is not None else None
    if cert_root is not None:
        cert_root.mkdir(parents=True, exist_ok=True)
    results = [
        run_case(
            case,
            c,
            determinism_check=determinism_check,
            max_width_search_vars=max_width_search_vars,
            export_cert_path=(cert_root / f"{case.name}.wcert") if cert_root is not None else None,
        )
        for case in case_list
    ]
    summary = summarize_results(results)
    return {
        "version": VERSION,
        "c_parameter": c,
        "scale": scale,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        "cases": [case.to_dict() for case in case_list],
        "per_case_results": [result.to_dict() for result in results],
        "summary": summary.to_dict(),
    }


def run_synthetic_benchmark(
    c: int,
    *,
    scale: str = "small",
    determinism_check: bool = False,
    max_width_search_vars: int = 28,
    timestamp: str | None = None,
    export_certs_dir: str | Path | None = None,
) -> dict[str, Any]:
    return run_benchmark(
        synthetic_cases(scale),
        c,
        determinism_check=determinism_check,
        max_width_search_vars=max_width_search_vars,
        timestamp=timestamp,
        scale=scale,
        export_certs_dir=export_certs_dir,
    )


def run_dimacs_dir_benchmark(
    dimacs_dir: str | Path,
    c: int,
    *,
    determinism_check: bool = False,
    max_width_search_vars: int = 28,
    timestamp: str | None = None,
    export_certs_dir: str | Path | None = None,
) -> dict[str, Any]:
    return run_benchmark(
        dimacs_cases(dimacs_dir),
        c,
        determinism_check=determinism_check,
        max_width_search_vars=max_width_search_vars,
        timestamp=timestamp,
        scale=None,
        export_certs_dir=export_certs_dir,
    )


def write_csv(data: dict[str, Any], path: str | Path) -> None:
    rows = data.get("per_case_results", [])
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Witnora-Core benchmark runner")
    parser.add_argument("--suite", choices=["synthetic"], help="benchmark suite to run")
    parser.add_argument(
        "--public-suite",
        choices=["cnfgen-small", "demo-cnfgen-artifact", "cnfgen-official", "satlib", "satcomp"],
        help="public benchmark suite to run",
    )
    parser.add_argument("--dimacs-dir", help="directory containing .cnf or .dimacs files")
    parser.add_argument("--cnfgen-path", help="optional official cnfgen executable path")
    parser.add_argument("--generated-dimacs-dir", help="directory for generated official CNFgen DIMACS files")
    parser.add_argument("--c", type=int, default=4, dest="c_parameter")
    parser.add_argument("--out", help="write JSON output to this path")
    parser.add_argument("--csv", dest="csv_path", help="write per-case CSV output to this path")
    parser.add_argument("--report", help="write Markdown benchmark report to this path")
    parser.add_argument("--export-certs", help="write one .wcert certificate per benchmark case")
    parser.add_argument("--drat-trim", help="optional drat-trim executable path for public UNSAT proof checking")
    parser.add_argument("--strict-unsat-external", action="store_true")
    parser.add_argument("--timeout-seconds", type=float, default=300.0)
    parser.add_argument("--max-instances", type=int)
    parser.add_argument(
        "--scale",
        choices=["small", "medium"],
        default="small",
        help="synthetic suite scale",
    )
    parser.add_argument("--determinism-check", action="store_true")
    parser.add_argument(
        "--max-width-search-vars",
        type=int,
        default=28,
        help="skip post-S exact width-order measurement above this variable count",
    )
    args = parser.parse_args(argv)

    if bool(args.suite) and (bool(args.public_suite) or bool(args.dimacs_dir)):
        parser.error("do not combine --suite with public benchmark options")
    if not args.suite and not args.public_suite and not args.dimacs_dir:
        parser.error("provide --suite synthetic, --public-suite, or --dimacs-dir")

    public_mode = bool(args.public_suite) or bool(args.dimacs_dir)
    if public_mode and not args.suite:
        from .public_benchmarks import (
            REASON_DIMACS_DIRECTORY_NOT_FOUND,
            REASON_SATCOMP_DIRECTORY_NOT_PROVIDED,
            REASON_SATLIB_DIRECTORY_NOT_PROVIDED,
            SOURCE_OFFICIAL_CNFGEN,
            SOURCE_SATCOMP_DIRECTORY,
            SOURCE_SATLIB_DIRECTORY,
            SUITE_RUN,
            dimacs_dir_cases as public_dimacs_dir_cases,
            generate_public_markdown_report,
            missing_suite_data,
            official_cnfgen_cases,
            public_suite_cases,
            run_public_benchmark,
            write_public_csv,
        )

        suite_name = args.public_suite or "dimacs-dir"
        suite_source_type = ""
        suite_status = SUITE_RUN
        not_run_reason = None
        if args.public_suite == "cnfgen-official":
            generated_dir = args.generated_dimacs_dir
            if generated_dir is None:
                base = Path(args.out).parent if args.out else Path(tempfile.mkdtemp(prefix="witnora-cnfgen-"))
                generated_dir = str(base / "generated_dimacs")
            cases, manifest = official_cnfgen_cases(
                generated_dir,
                cnfgen_path=args.cnfgen_path,
                max_instances=args.max_instances,
            )
            suite_source_type = SOURCE_OFFICIAL_CNFGEN
            suite_status = str(manifest.get("suite_status", SUITE_RUN))
            not_run_reason = manifest.get("not_run_reason")
            if suite_status != SUITE_RUN:
                data = missing_suite_data(
                    "cnfgen-official",
                    str(not_run_reason),
                    SOURCE_OFFICIAL_CNFGEN,
                    args.c_parameter,
                    timeout_seconds=args.timeout_seconds,
                    max_width_search_vars=args.max_width_search_vars,
                    strict_unsat_external=args.strict_unsat_external,
                    drat_trim_path=args.drat_trim,
                    message=str(manifest.get("instructions", "")),
                )
            else:
                data = run_public_benchmark(
                    cases,
                    args.c_parameter,
                    timeout_seconds=args.timeout_seconds,
                    max_width_search_vars=args.max_width_search_vars,
                    strict_unsat_external=args.strict_unsat_external,
                    drat_trim_path=args.drat_trim,
                    export_certs_dir=args.export_certs,
                    suite_name=suite_name,
                    suite_source_type=suite_source_type,
                    suite_status=suite_status,
                    not_run_reason=not_run_reason,
                )
                data["generation_manifest"] = manifest
        elif args.public_suite in {"satlib", "satcomp"}:
            source_type = SOURCE_SATLIB_DIRECTORY if args.public_suite == "satlib" else SOURCE_SATCOMP_DIRECTORY
            missing_reason = (
                REASON_SATLIB_DIRECTORY_NOT_PROVIDED
                if args.public_suite == "satlib"
                else REASON_SATCOMP_DIRECTORY_NOT_PROVIDED
            )
            if not args.dimacs_dir:
                data = missing_suite_data(
                    args.public_suite,
                    missing_reason,
                    source_type,
                    args.c_parameter,
                    timeout_seconds=args.timeout_seconds,
                    max_width_search_vars=args.max_width_search_vars,
                    strict_unsat_external=args.strict_unsat_external,
                    drat_trim_path=args.drat_trim,
                    message="Provide --dimacs-dir with public DIMACS CNF files.",
                )
            elif not Path(args.dimacs_dir).exists():
                data = missing_suite_data(
                    args.public_suite,
                    REASON_DIMACS_DIRECTORY_NOT_FOUND,
                    source_type,
                    args.c_parameter,
                    timeout_seconds=args.timeout_seconds,
                    max_width_search_vars=args.max_width_search_vars,
                    strict_unsat_external=args.strict_unsat_external,
                    drat_trim_path=args.drat_trim,
                    message=f"DIMACS directory not found: {args.dimacs_dir}",
                )
            else:
                cases = public_dimacs_dir_cases(
                    args.dimacs_dir,
                    source_suite=args.public_suite,
                    source_type=source_type,
                    max_instances=args.max_instances,
                )
                data = run_public_benchmark(
                    cases,
                    args.c_parameter,
                    timeout_seconds=args.timeout_seconds,
                    max_width_search_vars=args.max_width_search_vars,
                    strict_unsat_external=args.strict_unsat_external,
                    drat_trim_path=args.drat_trim,
                    export_certs_dir=args.export_certs,
                    suite_name=args.public_suite,
                    suite_source_type=source_type,
                )
        elif args.public_suite:
            cases = public_suite_cases(args.public_suite, max_instances=args.max_instances)
            source_type = "BUILT_IN_DEMO" if args.public_suite.startswith("demo-") or args.public_suite == "cnfgen-small" else ""
            data = run_public_benchmark(
                cases,
                args.c_parameter,
                timeout_seconds=args.timeout_seconds,
                max_width_search_vars=args.max_width_search_vars,
                strict_unsat_external=args.strict_unsat_external,
                drat_trim_path=args.drat_trim,
                export_certs_dir=args.export_certs,
                suite_name=args.public_suite,
                suite_source_type=source_type,
            )
        else:
            cases = public_dimacs_dir_cases(
                args.dimacs_dir,
                source_suite="dimacs-dir",
                max_instances=args.max_instances,
            )
            data = run_public_benchmark(
                cases,
                args.c_parameter,
                timeout_seconds=args.timeout_seconds,
                max_width_search_vars=args.max_width_search_vars,
                strict_unsat_external=args.strict_unsat_external,
                drat_trim_path=args.drat_trim,
                export_certs_dir=args.export_certs,
                suite_name="dimacs-dir",
                suite_source_type="DIMACS_DIRECTORY",
            )
        payload = json.dumps(data, indent=2, sort_keys=True)
        if args.out:
            Path(args.out).write_text(payload + "\n", encoding="utf-8")
        else:
            print(payload)
        if args.csv_path:
            write_public_csv(data, args.csv_path)
        if args.report:
            Path(args.report).write_text(generate_public_markdown_report(data), encoding="utf-8")
        if args.strict_unsat_external and not data.get("strict_unsat_external_pass", False):
            return 2
        return 0

    if args.suite == "synthetic":
        data = run_synthetic_benchmark(
            args.c_parameter,
            scale=args.scale,
            determinism_check=args.determinism_check,
            max_width_search_vars=args.max_width_search_vars,
            export_certs_dir=args.export_certs,
        )
    else:
        data = run_dimacs_dir_benchmark(
            args.dimacs_dir,
            args.c_parameter,
            determinism_check=args.determinism_check,
            max_width_search_vars=args.max_width_search_vars,
            export_certs_dir=args.export_certs,
        )

    payload = json.dumps(data, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    if args.csv_path:
        write_csv(data, args.csv_path)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
