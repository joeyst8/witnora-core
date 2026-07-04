"""CLI and programmatic entry point for Witnora-Core v0."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .certificate import (
    CollapsePath,
    NO_COLLAPSE,
    RECONSTRUCTION_FAILURE,
    SAT,
    UNSAT,
    XOR_UNSAT_NATIVE,
    StepLogger,
)
from .cnf import CNFFormula, formula_satisfied
from .components import component_details, connected_components
from .dimacs import load_dimacs, parse_dimacs
from .proof import export_certificate_bundle
from .primal import graph_edges, primal_graph
from .reconstruction import reconstruct_assignment
from .simplify import simplify
from .treewidth import find_elimination_order, verify_elimination_order
from .two_sat import solve_2sat
from .ve import run_variable_elimination
from .verifier import verify_collapse_path
from .xor import (
    XorSystem,
    detect_cnf_xor_patterns,
    parse_xor_lines,
    reconstruct_assignment as reconstruct_xor_assignment,
    solve_xor_system_gaussian,
    verify_xor_assignment,
    xor_metadata,
)


@dataclass
class _SolveResult:
    status: str
    final_formula: CNFFormula
    final_class: str
    final_assignment: dict[int, bool]
    component_results: list[dict[str, Any]]


def _leaf_result(
    component_id: str | None,
    component_formula: CNFFormula,
    status: str,
    final_formula: CNFFormula,
    final_class: str,
    assignment: dict[int, bool] | None = None,
    component_results: list[dict[str, Any]] | None = None,
) -> _SolveResult:
    assignment = assignment or {}
    results = list(component_results or [])
    if component_id is not None:
        results.append(
            {
                "component_id": component_id,
                "status": status,
                "final_class": final_class,
                "formula_hash": component_formula.formula_hash,
                "assignment": dict(assignment),
            }
        )
    return _SolveResult(status, final_formula, final_class, assignment, results)


def _stats(original: CNFFormula, logger: StepLogger, start: float) -> dict[str, Any]:
    return {
        "num_original_vars": original.num_vars,
        "num_original_clauses": original.num_clauses,
        "num_clauses_removed": sum(len(step.removed_clauses) for step in logger.steps),
        "num_clauses_added": sum(len(step.added_clauses) for step in logger.steps),
        "num_vars_eliminated": sum(1 for step in logger.steps if step.type == "VE"),
        "collapse_path_length": len(logger.steps),
        "time_ms": round((time.perf_counter() - start) * 1000.0, 3),
    }


def _component_id(parent_component_id: str | None, index: int) -> str:
    return str(index) if parent_component_id is None else f"{parent_component_id}.{index}"


def _component_details_with_ids(
    formula: CNFFormula, parent_component_id: str | None
) -> dict[str, Any]:
    details = component_details(formula)
    details["parent_component_id"] = parent_component_id
    for idx, component in enumerate(details["components"]):
        component["component_id"] = _component_id(parent_component_id, idx)
    return details


def _annotate_component_steps(logger: StepLogger, start_idx: int, component_id: str | None) -> None:
    if component_id is None:
        return
    for step in logger.steps[start_idx:]:
        step.details.setdefault("component_id", component_id)
        step.reconstruction_data.setdefault("component_id", component_id)


def _merge_assignments(
    merged: dict[int, bool], incoming: dict[int, bool]
) -> tuple[bool, str | None]:
    for var, value in incoming.items():
        if var in merged and merged[var] != value:
            return False, f"conflicting component assignment for variable {var}"
        merged[var] = value
    return True, None


def _union_formula(formulas: list[CNFFormula]) -> CNFFormula:
    return CNFFormula(clause for formula in formulas for clause in formula.clauses)


def _solve_component_group(
    formula: CNFFormula,
    c: int,
    logger: StepLogger,
    parent_component_id: str | None,
) -> _SolveResult:
    components = connected_components(formula)
    if len(components) <= 1:
        return _solve_context(formula, c, logger, parent_component_id, prefer_2sat=True)

    details = _component_details_with_ids(formula, parent_component_id)
    logger.append(
        "CD",
        formula,
        formula,
        details=details,
        reconstruction_data={
            "parent_component_id": parent_component_id,
            "component_ids": [item["component_id"] for item in details["components"]],
        },
    )

    states = {
        str(details["components"][idx]["component_id"]): component
        for idx, component in enumerate(components)
    }
    results: list[_SolveResult] = []
    merged_assignment: dict[int, bool] = {}

    for idx, component in enumerate(components):
        child_id = str(details["components"][idx]["component_id"])
        result = _solve_context(component, c, logger, child_id, prefer_2sat=True)
        states[child_id] = result.final_formula
        if result.status == SAT:
            ok, _error = _merge_assignments(merged_assignment, result.final_assignment)
            if not ok:
                final_formula = _union_formula([states[key] for key in sorted(states)])
                component_results = [
                    component_result
                    for item in results + [result]
                    for component_result in item.component_results
                ]
                return _leaf_result(
                    parent_component_id,
                    formula,
                    RECONSTRUCTION_FAILURE,
                    final_formula,
                    "CONFLICT",
                    {},
                    component_results,
                )
        results.append(result)

    final_formula = _union_formula([states[key] for key in sorted(states)])
    component_results = [
        component_result
        for item in results
        for component_result in item.component_results
    ]
    if any(result.status == UNSAT for result in results):
        return _leaf_result(
            parent_component_id,
            formula,
            UNSAT,
            final_formula,
            "CONFLICT",
            {},
            component_results,
        )
    if any(result.status == NO_COLLAPSE for result in results):
        return _leaf_result(
            parent_component_id,
            formula,
            NO_COLLAPSE,
            final_formula,
            "UNRESOLVED",
            {},
            component_results,
        )
    return _leaf_result(
        parent_component_id,
        formula,
        SAT,
        final_formula,
        "COMPONENTS_SOLVED",
        merged_assignment,
        component_results,
    )


def _solve_2sat_context(
    formula: CNFFormula,
    logger: StepLogger,
    component_id: str | None,
) -> _SolveResult:
    start_idx = len(logger.steps)
    result = solve_2sat(formula, logger)
    _annotate_component_steps(logger, start_idx, component_id)
    if result["status"] == "SAT":
        return _leaf_result(component_id, formula, SAT, formula, "2SAT", result["assignment"])
    return _leaf_result(component_id, formula, UNSAT, formula, "CONFLICT", {})


def _solve_treewidth_context(
    formula: CNFFormula,
    c: int,
    logger: StepLogger,
    component_id: str | None,
) -> _SolveResult:
    graph = primal_graph(formula)
    order = find_elimination_order(graph, c)
    if order is None:
        return _leaf_result(component_id, formula, NO_COLLAPSE, formula, "UNRESOLVED", {})

    width = verify_elimination_order(graph, order)
    details: dict[str, Any] = {
        "elimination_order": order,
        "width_observed": width,
        "width_cap": c,
        "primal_vertices": list(sorted(graph)),
        "primal_edges": [list(edge) for edge in graph_edges(graph)],
    }
    reconstruction_data: dict[str, Any] = {"elimination_order": order}
    if component_id is not None:
        details["component_id"] = component_id
        reconstruction_data["component_id"] = component_id
    logger.append(
        "TREEWIDTH_SOLVE",
        formula,
        formula,
        details=details,
        reconstruction_data=reconstruction_data,
    )

    start_idx = len(logger.steps)
    ve_status, final_formula, _details = run_variable_elimination(formula, order, c, logger)
    _annotate_component_steps(logger, start_idx, component_id)
    if ve_status == NO_COLLAPSE:
        return _leaf_result(component_id, formula, NO_COLLAPSE, final_formula, "UNRESOLVED", {})
    if final_formula.contains_empty_clause or ve_status == "UNSAT":
        return _leaf_result(component_id, formula, UNSAT, final_formula, "CONFLICT", {})
    if final_formula.is_empty:
        return _leaf_result(component_id, formula, SAT, final_formula, "TREEWIDTH_LEQ_C", {})
    if final_formula.is_2cnf:
        tail = _solve_2sat_context(final_formula, logger, component_id)
        if tail.status == SAT:
            return _leaf_result(
                component_id,
                formula,
                SAT,
                final_formula,
                "TREEWIDTH_LEQ_C",
                tail.final_assignment,
                tail.component_results[:-1] if component_id is not None else tail.component_results,
            )
        return tail
    return _leaf_result(component_id, formula, NO_COLLAPSE, final_formula, "UNRESOLVED", {})


def _solve_context(
    formula: CNFFormula,
    c: int,
    logger: StepLogger,
    component_id: str | None,
    *,
    prefer_2sat: bool,
) -> _SolveResult:
    if formula.contains_empty_clause:
        return _leaf_result(component_id, formula, UNSAT, formula, "CONFLICT", {})
    if formula.is_empty:
        return _leaf_result(component_id, formula, SAT, formula, "EMPTY", {})

    components = connected_components(formula)
    if len(components) > 1:
        return _solve_component_group(formula, c, logger, component_id)

    if prefer_2sat and formula.is_2cnf:
        return _solve_2sat_context(formula, logger, component_id)

    start_idx = len(logger.steps)
    simplified, simplify_status = simplify(
        formula,
        logger,
        log_component_decomposition=False,
    )
    _annotate_component_steps(logger, start_idx, component_id)

    if simplify_status == "UNSAT" or simplified.contains_empty_clause:
        return _leaf_result(component_id, formula, UNSAT, simplified, "CONFLICT", {})
    if simplified.is_empty:
        return _leaf_result(component_id, formula, SAT, simplified, "EMPTY", {})

    components = connected_components(simplified)
    if len(components) > 1:
        return _solve_component_group(simplified, c, logger, component_id)

    if simplified.is_2cnf:
        return _solve_2sat_context(simplified, logger, component_id)

    return _solve_treewidth_context(simplified, c, logger, component_id)


def _finalize(
    original: CNFFormula,
    c: int,
    logger: StepLogger,
    final_formula: CNFFormula,
    final_class: str,
    status: str,
    final_assignment: dict[int, bool] | None,
    component_results: list[dict[str, Any]] | None,
    start: float,
) -> CollapsePath:
    reconstructed: dict[int, bool] = {}
    original_verification = False
    component_results = list(component_results or [])

    if status == SAT:
        result = reconstruct_assignment(original, logger.steps, final_assignment or {})
        if result.ok:
            reconstructed = result.assignment
            original_verification = True
        else:
            status = RECONSTRUCTION_FAILURE
            reconstructed = result.assignment
            original_verification = False

    if status == SAT and reconstructed and component_results:
        component_vars: dict[str, set[int]] = {}
        for step in logger.steps:
            if step.type != "CD":
                continue
            for component in step.details.get("components", []):
                component_vars[str(component["component_id"])] = {
                    int(var) for var in component.get("variables", [])
                }
        updated_component_results: list[dict[str, Any]] = []
        for result in component_results:
            item = dict(result)
            variables = component_vars.get(str(item.get("component_id")), set())
            if item.get("status") == SAT:
                item["assignment"] = {
                    var: reconstructed[var]
                    for var in sorted(variables)
                    if var in reconstructed
                }
            updated_component_results.append(item)
        component_results = updated_component_results

    path = CollapsePath(
        original_formula_hash=original.formula_hash,
        c_parameter=c,
        steps=logger.steps,
        final_formula_hash=final_formula.formula_hash,
        final_class=final_class,
        status=status,
        final_assignment=final_assignment or {},
        reconstructed_original_assignment=reconstructed,
        original_verification=original_verification,
        component_results=component_results,
        stats=_stats(original, logger, start),
    )

    if status in {SAT, UNSAT}:
        verification = verify_collapse_path(original, path)
        if not verification.ok:
            path.status = RECONSTRUCTION_FAILURE
            path.original_verification = False
            path.stats["verification_errors"] = verification.errors
    return path


def solve(formula: CNFFormula, c: int = 4) -> CollapsePath:
    if c < 0 or c > 4:
        raise ValueError("Witnora-Core v0 supports c in the range 0..4")

    start = time.perf_counter()
    original = formula
    logger = StepLogger()

    result = _solve_context(original, c, logger, None, prefer_2sat=False)
    return _finalize(
        original,
        c,
        logger,
        result.final_formula,
        result.final_class,
        result.status,
        result.final_assignment,
        result.component_results,
        start,
    )


def _unit_assignments(formula: CNFFormula) -> dict[int, bool] | None:
    assignment: dict[int, bool] = {}
    for clause in formula.clauses:
        if len(clause) != 1:
            continue
        lit = clause.literals[0]
        var = abs(lit)
        value = lit > 0
        if var in assignment and assignment[var] != value:
            return None
        assignment[var] = value
    return assignment


def _xor_native_unsat_path(
    formula: CNFFormula,
    c: int,
    system: XorSystem,
    solution: dict[str, Any],
    start: float,
    *,
    detected_system: XorSystem | None = None,
) -> CollapsePath:
    return CollapsePath(
        original_formula_hash=formula.formula_hash,
        c_parameter=c,
        steps=[],
        final_formula_hash=formula.formula_hash,
        final_class="XOR_UNSAT_NATIVE",
        status=XOR_UNSAT_NATIVE,
        final_assignment={},
        reconstructed_original_assignment={},
        original_verification=False,
        component_results=[],
        stats={
            "num_original_vars": formula.num_vars,
            "num_original_clauses": formula.num_clauses,
            "num_clauses_removed": 0,
            "num_clauses_added": 0,
            "num_vars_eliminated": 0,
            "collapse_path_length": 0,
            "time_ms": round((time.perf_counter() - start) * 1000.0, 3),
        },
        xor_data=xor_metadata(system, solution, verified=True, detected_system=detected_system),
    )


def solve_with_xor(
    formula: CNFFormula,
    c: int = 4,
    *,
    xor_system: XorSystem | None = None,
    detect_cnf_xor: bool = False,
) -> CollapsePath:
    """Solve a CNF together with conservative explicit/detected XOR equations."""

    start = time.perf_counter()
    sidecar = xor_system or XorSystem()
    detected = detect_cnf_xor_patterns(formula) if detect_cnf_xor else XorSystem()
    system = XorSystem([*sidecar.equations, *detected.equations])
    if not system.equations:
        return solve(formula, c)

    xor_solution = solve_xor_system_gaussian(system)
    if xor_solution["status"] == "UNSAT":
        return _xor_native_unsat_path(
            formula,
            c,
            system,
            xor_solution,
            start,
            detected_system=detected,
        )

    unit_assignment = _unit_assignments(formula)
    if unit_assignment is None:
        contradiction = {
            "status": "UNSAT",
            "assignment": {},
            "rank": 0,
            "pivot_variables": [],
            "free_variables": [],
            "forced_assignments": {},
            "elimination_trace": [{"type": "cnf_unit_conflict"}],
            "contradiction": {"variables": [], "rhs": 1},
        }
        return _xor_native_unsat_path(formula, c, system, contradiction, start, detected_system=detected)
    if unit_assignment:
        restricted = solve_xor_system_gaussian(system.substitute(unit_assignment))
        if restricted["status"] == "UNSAT":
            return _xor_native_unsat_path(
                formula,
                c,
                system,
                restricted,
                start,
                detected_system=detected,
            )

    cnf_path = solve(formula, c)
    xor_assignment = reconstruct_xor_assignment(xor_solution)

    if cnf_path.status == UNSAT:
        cnf_path.xor_data = xor_metadata(system, xor_solution, verified=False, detected_system=detected)
        return cnf_path

    candidate_assignments: list[dict[int, bool]] = []
    if cnf_path.status == SAT:
        base = dict(cnf_path.reconstructed_original_assignment)
        restricted = solve_xor_system_gaussian(system.substitute(base))
        if restricted["status"] == "SAT":
            merged = dict(base)
            merged.update(reconstruct_xor_assignment(restricted))
            candidate_assignments.append(merged)
    candidate_assignments.append(dict(xor_assignment))

    for assignment in candidate_assignments:
        for var in formula.variables:
            assignment.setdefault(var, False)
        if formula_satisfied(formula, assignment) and verify_xor_assignment(system, assignment):
            if cnf_path.status == SAT:
                path = cnf_path
            else:
                path = CollapsePath(
                    original_formula_hash=formula.formula_hash,
                    c_parameter=c,
                    steps=[],
                    final_formula_hash=formula.formula_hash,
                    final_class="XOR_AFFINE",
                    status=SAT,
                    final_assignment=assignment,
                    reconstructed_original_assignment=assignment,
                    original_verification=True,
                    component_results=[],
                    stats={
                        "num_original_vars": formula.num_vars,
                        "num_original_clauses": formula.num_clauses,
                        "num_clauses_removed": 0,
                        "num_clauses_added": 0,
                        "num_vars_eliminated": 0,
                        "collapse_path_length": 0,
                        "time_ms": round((time.perf_counter() - start) * 1000.0, 3),
                    },
                )
            path.final_class = "CNF_XOR_COMBINED" if formula.clauses else "XOR_AFFINE"
            path.status = SAT
            path.final_assignment = assignment
            path.reconstructed_original_assignment = assignment
            path.original_verification = True
            verified_solution = dict(xor_solution)
            verified_solution["assignment"] = {str(var): bool(value) for var, value in sorted(assignment.items())}
            path.xor_data = xor_metadata(system, verified_solution, verified=True, detected_system=detected)
            return path

    cnf_path.xor_data = xor_metadata(system, xor_solution, verified=False, detected_system=detected)
    if cnf_path.status == SAT:
        cnf_path.status = NO_COLLAPSE
        cnf_path.final_class = "UNRESOLVED"
        cnf_path.original_verification = False
    return cnf_path


def solve_dimacs_file(path: str | Path, c: int = 4) -> CollapsePath:
    return solve(load_dimacs(path), c)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Witnora-Core v0 collapse-path runner")
    parser.add_argument("dimacs", help="path to DIMACS CNF input")
    parser.add_argument("--c", "-c", type=int, default=4, dest="c_parameter")
    parser.add_argument("--export-cert", help="write .wcert directory or .wcert.json certificate")
    parser.add_argument("--xor", help="optional sidecar file containing explicit XOR equations")
    parser.add_argument(
        "--detect-xor",
        action="store_true",
        help="enable conservative exact CNF XOR pattern detection",
    )
    parser.add_argument(
        "--export-drat",
        action="store_true",
        help="with --export-cert, add proof.drat for supported UNSAT paths",
    )
    parser.add_argument(
        "--drat-trim",
        help="optional drat-trim executable path for external proof.drat verification",
    )
    args = parser.parse_args(argv)
    dimacs_path = Path(args.dimacs)
    original_text = dimacs_path.read_text(encoding="utf-8")
    formula = parse_dimacs(original_text)
    xor_system = None
    if args.xor:
        xor_system = parse_xor_lines(Path(args.xor).read_text(encoding="utf-8"))
    path = solve_with_xor(
        formula,
        args.c_parameter,
        xor_system=xor_system,
        detect_cnf_xor=args.detect_xor,
    ) if (xor_system is not None or args.detect_xor) else solve(formula, args.c_parameter)
    if args.export_cert:
        export_certificate_bundle(
            formula,
            path,
            args.export_cert,
            original_dimacs_text=original_text,
            export_drat=args.export_drat,
            drat_trim_path=args.drat_trim,
        )
    print(json.dumps(path.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
