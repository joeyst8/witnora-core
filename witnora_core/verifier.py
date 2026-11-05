"""Replay verifier for Witnora collapse paths."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .bce import blocked_clause_proof, find_first_blocked_clause
from .certificate import CollapsePath, CollapseStep, SAT, UNSAT
from .cnf import CNFFormula, Clause, formula_satisfied
from .components import component_details
from .primal import graph_edges, primal_graph
from .simplify import _pure_literal_step, _unit_step
from .subsumption import find_first_subsumption
from .treewidth import verify_elimination_order
from .two_sat import solve_2sat
from .ve import eliminate_variable


@dataclass
class VerificationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)


def _clauses_equal(a: Iterable[list[int]], b: Iterable[list[int]]) -> bool:
    return sorted([list(item) for item in a]) == sorted([list(item) for item in b])


def _component_signature(component: dict) -> dict:
    return {
        "formula_hash": component.get("formula_hash"),
        "variables": list(component.get("variables", [])),
        "clauses": [list(clause) for clause in component.get("clauses", [])],
        "clause_indices": list(component.get("clause_indices", [])),
    }


def _formula_from_component_states(states: dict[str, CNFFormula]) -> CNFFormula:
    return CNFFormula(
        clause
        for component_id in sorted(states)
        for clause in states[component_id].clauses
    )


def _verify_cd_step(
    step: CollapseStep,
    current: CNFFormula,
) -> tuple[bool, dict[str, CNFFormula], str | None]:
    expected = component_details(current)
    logged_components = step.details.get("components", [])

    if step.output_formula_hash != current.formula_hash:
        return False, {}, "CD output hash mismatch"
    if step.details.get("component_count") != expected["component_count"]:
        return False, {}, "CD component count mismatch"
    if step.details.get("incidence_edges") != expected["incidence_edges"]:
        return False, {}, "CD incidence edges mismatch"

    expected_sigs = [_component_signature(item) for item in expected["components"]]
    logged_sigs = [_component_signature(item) for item in logged_components]
    if expected_sigs != logged_sigs:
        return False, {}, "CD component contents mismatch"

    all_clause_indices: list[int] = []
    owner_by_var: dict[int, str] = {}
    child_states: dict[str, CNFFormula] = {}
    for logged in logged_components:
        component_id = str(logged.get("component_id"))
        if component_id in child_states:
            return False, {}, "CD duplicate component id"
        variables = {int(var) for var in logged.get("variables", [])}
        clause_indices = [int(idx) for idx in logged.get("clause_indices", [])]
        all_clause_indices.extend(clause_indices)
        for var in variables:
            previous = owner_by_var.get(var)
            if previous is not None and previous != component_id:
                return False, {}, "CD variable sets are not disjoint"
            owner_by_var[var] = component_id
        for raw_clause in logged.get("clauses", []):
            clause = Clause(raw_clause)
            if not set(clause.variables).issubset(variables):
                return False, {}, "CD clause crosses component variable set"
        child_states[component_id] = CNFFormula(logged.get("clauses", []))

    if sorted(all_clause_indices) != list(range(len(current.clauses))):
        return False, {}, "CD clauses are not an exact partition"

    return True, child_states, None


def _verify_up(step: CollapseStep, current: CNFFormula) -> tuple[bool, CNFFormula, str | None]:
    computed = _unit_step(current)
    if computed is None:
        return False, current, "UP step has no unit clause"
    output, details = computed
    removed = details["satisfied_clauses"] + [item["from"] for item in details["shortened_clauses"]]
    added = [item["to"] for item in details["shortened_clauses"]]
    if step.assigned_literals != [details["assigned_literal"]]:
        return False, current, "UP assigned literal mismatch"
    if not _clauses_equal(step.removed_clauses, removed) or not _clauses_equal(step.added_clauses, added):
        return False, current, "UP removed/added clauses mismatch"
    if step.output_formula_hash != output.formula_hash:
        return False, current, "UP output hash mismatch"
    return True, output, None


def _verify_ple(step: CollapseStep, current: CNFFormula) -> tuple[bool, CNFFormula, str | None]:
    computed = _pure_literal_step(current)
    if computed is None:
        return False, current, "PLE step has no pure literal"
    output, details = computed
    if step.assigned_literals != [details["assigned_literal"]]:
        return False, current, "PLE assigned literal mismatch"
    if not _clauses_equal(step.removed_clauses, details["removed_due_to_pure_literal"]):
        return False, current, "PLE removed clauses mismatch"
    if step.output_formula_hash != output.formula_hash:
        return False, current, "PLE output hash mismatch"
    return True, output, None


def _verify_sub(step: CollapseStep, current: CNFFormula) -> tuple[bool, CNFFormula, str | None]:
    found = find_first_subsumption(current)
    if found is None:
        return False, current, "SUB step has no valid subsumption"
    subsumer, removed = found
    output = current.without_clause(removed)
    if step.details.get("subsuming_clause") != subsumer.to_list():
        return False, current, "SUB subsuming clause mismatch"
    if step.removed_clauses != [removed.to_list()]:
        return False, current, "SUB removed clause mismatch"
    if step.output_formula_hash != output.formula_hash:
        return False, current, "SUB output hash mismatch"
    return True, output, None


def _verify_bce(step: CollapseStep, current: CNFFormula) -> tuple[bool, CNFFormula, str | None]:
    found = find_first_blocked_clause(current)
    if found is None:
        return False, current, "BCE step has no blocked clause"
    removed, proof = found
    if step.removed_clauses != [removed.to_list()]:
        return False, current, "BCE removed clause mismatch"
    if step.details.get("blocked_literal") != proof["blocked_literal"]:
        return False, current, "BCE blocked literal mismatch"
    recomputed = blocked_clause_proof(current, removed, proof["blocked_literal"])
    if recomputed is None:
        return False, current, "BCE proof did not replay"
    if step.details.get("proof_digest") != recomputed["proof_digest"]:
        return False, current, "BCE proof digest mismatch"
    output = current.without_clause(removed)
    if step.output_formula_hash != output.formula_hash:
        return False, current, "BCE output hash mismatch"
    return True, output, None


def _verify_ve(step: CollapseStep, current: CNFFormula, c: int) -> tuple[bool, CNFFormula, str | None]:
    var = int(step.reconstruction_data.get("eliminated_variable", 0))
    status, output, details = eliminate_variable(current, var, c, logger=None)
    if status != "OK":
        return False, current, "VE replay failed"
    if step.output_formula_hash != output.formula_hash:
        return False, current, "VE output hash mismatch"
    expected_removed = [clause.to_list() for clause in sorted(
        [clause for clause in current.clauses if var in clause or -var in clause],
        key=lambda c_: c_.literals,
    )]
    if not _clauses_equal(step.removed_clauses, expected_removed):
        return False, current, "VE removed clauses mismatch"
    if not _clauses_equal(step.added_clauses, details.get("added_resolvents", [])):
        return False, current, "VE added resolvents mismatch"
    if details.get("width_observed", 0) > c:
        return False, current, "VE width cap exceeded"
    return True, output, None


def verify_collapse_path(original: CNFFormula, path: CollapsePath) -> VerificationResult:
    errors: list[str] = []
    current = original
    component_states: dict[str, CNFFormula] = {}
    component_original_vars: dict[str, set[int]] = {}
    component_original_formulas: dict[str, CNFFormula] = {}
    saw_unsat_2sat = False

    if path.original_formula_hash != original.formula_hash:
        errors.append("original formula hash mismatch")

    expected_step_id = 1
    for step in path.steps:
        if step.step_id != expected_step_id:
            errors.append(f"step id mismatch at {step.step_id}")
            break
        expected_step_id += 1

        context_id = step.details.get("component_id")
        parent_context_id = step.details.get("parent_component_id") if step.type == "CD" else None
        if context_id is not None:
            context_id = str(context_id)
        if parent_context_id is not None:
            parent_context_id = str(parent_context_id)

        if step.type == "CD":
            context_formula = current if parent_context_id is None else component_states.get(parent_context_id)
            if context_formula is None:
                errors.append(f"step {step.step_id}: CD parent component is missing")
                break
        elif context_id is not None:
            context_formula = component_states.get(context_id)
            if context_formula is None:
                errors.append(f"step {step.step_id}: component {context_id} is missing")
                break
        else:
            if component_states:
                errors.append(f"step {step.step_id}: component-local step missing component_id")
                break
            context_formula = current

        if step.input_formula_hash != context_formula.formula_hash:
            errors.append(f"{step.type} input hash mismatch at step {step.step_id}")
            break

        if step.type == "UP":
            ok, next_formula, error = _verify_up(step, context_formula)
        elif step.type == "PLE":
            ok, next_formula, error = _verify_ple(step, context_formula)
        elif step.type == "SUB":
            ok, next_formula, error = _verify_sub(step, context_formula)
        elif step.type == "BCE":
            ok, next_formula, error = _verify_bce(step, context_formula)
        elif step.type == "CD":
            ok, child_states, error = _verify_cd_step(step, context_formula)
            next_formula = context_formula
            if ok:
                if parent_context_id is not None:
                    component_states.pop(parent_context_id, None)
                    component_original_vars.pop(parent_context_id, None)
                for child_id, child_formula in child_states.items():
                    component_states[child_id] = child_formula
                    component_original_vars[child_id] = set(child_formula.variables)
                    component_original_formulas[child_id] = child_formula
        elif step.type == "TREEWIDTH_SOLVE":
            graph = primal_graph(context_formula)
            order = [int(var) for var in step.details.get("elimination_order", [])]
            width = verify_elimination_order(graph, order)
            ok = (
                width is not None
                and width <= path.c_parameter
                and step.output_formula_hash == context_formula.formula_hash
                and step.details.get("primal_edges") == [list(edge) for edge in graph_edges(graph)]
            )
            error = None if ok else "TREEWIDTH_SOLVE order verification failed"
            next_formula = context_formula
        elif step.type == "VE":
            ok, next_formula, error = _verify_ve(step, context_formula, path.c_parameter)
        elif step.type == "2SAT_SOLVE":
            try:
                result = solve_2sat(context_formula, logger=None)
            except Exception as exc:  # pragma: no cover - defensive certification path
                ok = False
                error = f"2SAT_SOLVE replay raised {exc}"
            else:
                ok = step.output_formula_hash == context_formula.formula_hash
                if result["status"] != step.details.get("status"):
                    ok = False
                    error = "2SAT_SOLVE status mismatch"
                elif result["status"] == "SAT":
                    logged = {int(k): bool(v) for k, v in step.details.get("assignment", {}).items()}
                    ok = ok and logged == result["assignment"]
                    error = None if ok else "2SAT_SOLVE assignment mismatch"
                else:
                    saw_unsat_2sat = True
                    error = None if ok else "2SAT_SOLVE hash mismatch"
            next_formula = context_formula
        else:
            ok = False
            error = f"unknown step type {step.type}"
            next_formula = context_formula

        if not ok:
            errors.append(f"step {step.step_id}: {error}")
            break

        if step.type != "CD":
            if context_id is None:
                current = next_formula
            else:
                component_states[context_id] = next_formula

    final_formula = _formula_from_component_states(component_states) if component_states else current

    if not errors and path.final_formula_hash != final_formula.formula_hash:
        errors.append("final formula hash mismatch")

    if not errors and component_original_vars:
        owner_by_var: dict[int, str] = {}
        for component_id, variables in component_original_vars.items():
            for var in variables:
                previous = owner_by_var.get(var)
                if previous is not None and previous != component_id:
                    errors.append("component variable partition conflict")
                    break
                owner_by_var[var] = component_id
            if errors:
                break
        final_assignment = {int(k): bool(v) for k, v in path.final_assignment.items()}
        for step in path.steps:
            if step.type != "2SAT_SOLVE" or step.details.get("status") != "SAT":
                continue
            logged = {int(k): bool(v) for k, v in step.details.get("assignment", {}).items()}
            for var, value in logged.items():
                if final_assignment.get(var) != value:
                    errors.append("component assignment merge mismatch")
                    break
            if errors:
                break

    if not errors and path.component_results:
        seen_component_ids: set[str] = set()
        component_assignment_merge: dict[int, bool] = {}
        statuses = [str(item.get("status")) for item in path.component_results]
        for item in path.component_results:
            component_id = str(item.get("component_id", ""))
            if component_id in seen_component_ids:
                errors.append("duplicate component_result id")
                break
            seen_component_ids.add(component_id)
            if component_original_formulas and component_id not in component_original_formulas:
                errors.append("component_result references unknown component")
                break
            if item.get("status") == SAT:
                assignment = {int(k): bool(v) for k, v in item.get("assignment", {}).items()}
                for var, value in assignment.items():
                    if var in component_assignment_merge and component_assignment_merge[var] != value:
                        errors.append("component_result assignments conflict")
                        break
                    component_assignment_merge[var] = value
                if errors:
                    break
                component_formula = component_original_formulas.get(component_id)
                if component_formula is not None and not formula_satisfied(component_formula, assignment):
                    errors.append("component_result SAT assignment does not satisfy component")
                    break
        if not errors:
            if UNSAT in statuses and path.status != UNSAT:
                errors.append("component_results contain UNSAT but full status is not UNSAT")
            elif "NO_COLLAPSE_FOUND_UNDER_CURRENT_GRAMMAR_AND_C" in statuses and path.status != "NO_COLLAPSE_FOUND_UNDER_CURRENT_GRAMMAR_AND_C":
                errors.append("component_results contain no-collapse but full status does not match")
            elif statuses and all(status == SAT for status in statuses):
                if path.status != SAT:
                    errors.append("all component_results are SAT but full status is not SAT")
                elif len(statuses) > 1 and path.final_class != "COMPONENTS_SOLVED":
                    errors.append("multi-component SAT did not use COMPONENTS_SOLVED final_class")
        if not errors and path.status == SAT:
            reconstructed = {
                int(k): bool(v)
                for k, v in path.reconstructed_original_assignment.items()
            }
            for var, value in component_assignment_merge.items():
                if reconstructed.get(var) != value:
                    errors.append("component_result assignment merge differs from reconstructed assignment")
                    break

    if not errors and path.status == SAT:
        assignment = {int(k): bool(v) for k, v in path.reconstructed_original_assignment.items()}
        if not path.original_verification or not formula_satisfied(original, assignment):
            errors.append("SAT assignment does not satisfy original formula")

    if not errors and path.status == UNSAT:
        if not final_formula.contains_empty_clause and not saw_unsat_2sat:
            errors.append("UNSAT certificate has no replayed contradiction")

    return VerificationResult(ok=not errors, errors=errors)
