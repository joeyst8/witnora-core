"""Benchmark and collapse-measurement layer for Witnora-Core."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
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
from .runner import solve
from .simplify import simplify
from .treewidth import find_elimination_order

VERSION = "0.1.0"


@dataclass(frozen=True)
class BenchmarkCase:
    name: str
    family: str
    formula: CNFFormula
    source: str
    notes: str = ""

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

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_name": self.case_name,
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
) -> BenchmarkResult:
    original = structural_metrics(case.formula)
    post_s = post_s_formula(case.formula)
    post = structural_metrics(post_s)
    path = solve(case.formula, c)

    determinism_pass: bool | None = None
    if determinism_check:
        second = solve(case.formula, c)
        determinism_pass = compare_deterministic_run(path, second)

    return BenchmarkResult(
        case_name=case.name,
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
        post_s_width_order_found=width_order_found_for_c(
            post_s,
            c,
            max_width_search_vars=max_width_search_vars,
        ),
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


def synthetic_cases() -> list[BenchmarkCase]:
    return [
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
) -> dict[str, Any]:
    case_list = list(cases)
    results = [
        run_case(
            case,
            c,
            determinism_check=determinism_check,
            max_width_search_vars=max_width_search_vars,
        )
        for case in case_list
    ]
    summary = summarize_results(results)
    return {
        "version": VERSION,
        "c_parameter": c,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        "cases": [case.to_dict() for case in case_list],
        "per_case_results": [result.to_dict() for result in results],
        "summary": summary.to_dict(),
    }


def run_synthetic_benchmark(
    c: int,
    *,
    determinism_check: bool = False,
    max_width_search_vars: int = 28,
    timestamp: str | None = None,
) -> dict[str, Any]:
    return run_benchmark(
        synthetic_cases(),
        c,
        determinism_check=determinism_check,
        max_width_search_vars=max_width_search_vars,
        timestamp=timestamp,
    )


def run_dimacs_dir_benchmark(
    dimacs_dir: str | Path,
    c: int,
    *,
    determinism_check: bool = False,
    max_width_search_vars: int = 28,
    timestamp: str | None = None,
) -> dict[str, Any]:
    return run_benchmark(
        dimacs_cases(dimacs_dir),
        c,
        determinism_check=determinism_check,
        max_width_search_vars=max_width_search_vars,
        timestamp=timestamp,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Witnora-Core benchmark runner")
    parser.add_argument("--suite", choices=["synthetic"], help="benchmark suite to run")
    parser.add_argument("--dimacs-dir", help="directory containing .cnf or .dimacs files")
    parser.add_argument("--c", type=int, default=4, dest="c_parameter")
    parser.add_argument("--out", help="write JSON output to this path")
    parser.add_argument("--determinism-check", action="store_true")
    parser.add_argument(
        "--max-width-search-vars",
        type=int,
        default=28,
        help="skip post-S exact width-order measurement above this variable count",
    )
    args = parser.parse_args(argv)

    if bool(args.suite) == bool(args.dimacs_dir):
        parser.error("provide exactly one of --suite synthetic or --dimacs-dir")

    if args.suite == "synthetic":
        data = run_synthetic_benchmark(
            args.c_parameter,
            determinism_check=args.determinism_check,
            max_width_search_vars=args.max_width_search_vars,
        )
    else:
        data = run_dimacs_dir_benchmark(
            args.dimacs_dir,
            args.c_parameter,
            determinism_check=args.determinism_check,
            max_width_search_vars=args.max_width_search_vars,
        )

    payload = json.dumps(data, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
