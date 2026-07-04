"""SAT witness reconstruction from collapse steps."""

from __future__ import annotations

from dataclasses import dataclass

from .certificate import CollapseStep
from .cnf import Clause, CNFFormula, formula_satisfied


@dataclass
class ReconstructionResult:
    ok: bool
    assignment: dict[int, bool]
    error: str | None = None


def _literal_true_default_false(lit: int, assignment: dict[int, bool]) -> bool:
    value = assignment.get(abs(lit), False)
    return value if lit > 0 else not value


def _clause_satisfied_default_false(clause: Clause, assignment: dict[int, bool]) -> bool:
    return any(_literal_true_default_false(lit, assignment) for lit in clause)


def _assign_literal_consistent(assignment: dict[int, bool], lit: int) -> str | None:
    var = abs(lit)
    value = lit > 0
    if var in assignment and assignment[var] != value:
        return f"inconsistent assignment for variable {var}"
    assignment[var] = value
    return None


def reconstruct_bce_step(assignment: dict[int, bool], step: CollapseStep) -> ReconstructionResult:
    data = step.reconstruction_data
    removed_clause = Clause(data["removed_clause"])
    blocked_literal = int(data["blocked_literal"])
    updated = dict(assignment)

    if not _clause_satisfied_default_false(removed_clause, updated):
        updated[abs(blocked_literal)] = blocked_literal > 0

    if not _clause_satisfied_default_false(removed_clause, updated):
        return ReconstructionResult(False, updated, "BCE removed clause remains unsatisfied")

    for raw_clause in data.get("opposite_clauses", []):
        clause = Clause(raw_clause)
        if not _clause_satisfied_default_false(clause, updated):
            return ReconstructionResult(False, updated, "BCE opposite clause was falsified")

    return ReconstructionResult(True, updated)


def reconstruct_ve_step(assignment: dict[int, bool], step: CollapseStep) -> ReconstructionResult:
    data = step.reconstruction_data
    var = int(data["eliminated_variable"])
    removed = [Clause(raw) for raw in data["removed_clauses"]]
    desired: bool | None = None

    for clause in removed:
        contains_pos = var in clause
        contains_neg = -var in clause
        if not contains_pos and not contains_neg:
            return ReconstructionResult(False, dict(assignment), "VE log contains unrelated clause")
        rest = [lit for lit in clause if abs(lit) != var]
        rest_satisfied = any(_literal_true_default_false(lit, assignment) for lit in rest)
        if rest_satisfied:
            continue
        needed = True if contains_pos else False
        if desired is not None and desired != needed:
            return ReconstructionResult(False, dict(assignment), "VE reconstruction sign conflict")
        desired = needed

    updated = dict(assignment)
    if desired is None:
        updated.setdefault(var, False)
    else:
        if var in updated and updated[var] != desired:
            return ReconstructionResult(False, updated, f"VE assignment conflict for variable {var}")
        updated[var] = desired

    for clause in removed:
        if not _clause_satisfied_default_false(clause, updated):
            return ReconstructionResult(False, updated, "VE removed clause remains unsatisfied")

    return ReconstructionResult(True, updated)


def reconstruct_assignment(
    original_formula: CNFFormula,
    steps: list[CollapseStep],
    final_assignment: dict[int, bool],
) -> ReconstructionResult:
    assignment = {int(var): bool(value) for var, value in final_assignment.items()}

    for step in reversed(steps):
        if step.type in {"2SAT_SOLVE", "TREEWIDTH_SOLVE", "SUB", "CD"}:
            continue
        if step.type in {"UP", "PLE"}:
            if not step.assigned_literals:
                return ReconstructionResult(False, assignment, f"{step.type} missing assigned literal")
            error = _assign_literal_consistent(assignment, int(step.assigned_literals[0]))
            if error:
                return ReconstructionResult(False, assignment, error)
            continue
        if step.type == "BCE":
            result = reconstruct_bce_step(assignment, step)
            if not result.ok:
                return result
            assignment = result.assignment
            continue
        if step.type == "VE":
            result = reconstruct_ve_step(assignment, step)
            if not result.ok:
                return result
            assignment = result.assignment
            continue
        return ReconstructionResult(False, assignment, f"unsupported reconstruction step {step.type}")

    for var in original_formula.variables:
        assignment.setdefault(var, False)

    if not formula_satisfied(original_formula, assignment):
        return ReconstructionResult(False, assignment, "reconstructed assignment does not satisfy original formula")
    return ReconstructionResult(True, assignment)
