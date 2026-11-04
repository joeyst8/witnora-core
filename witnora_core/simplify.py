"""Deterministic simplifier S."""

from __future__ import annotations

from typing import Any

from .bce import find_first_blocked_clause
from .certificate import StepLogger
from .cnf import CNFFormula, Clause, literal_sort_key
from .components import component_details
from .subsumption import find_first_subsumption


def _unit_step(formula: CNFFormula, *,
               backend: str = "python") -> tuple[CNFFormula, dict[str, Any]] | None:
    if backend == "rust":
        from witnora_ve import unit_step_native
        got = unit_step_native(formula.to_clause_lists())
        if got is None:
            return None
        output, lit, satisfied, shortened, conflict = got
        return CNFFormula(output), {
            "assigned_literal": lit, "unit_clause": [lit],
            "satisfied_clauses": satisfied,
            "shortened_clauses": [
                {"from": old, "to": new} for old, new in shortened
            ],
            "conflict": conflict,
        }
    if backend != "python":
        raise ValueError("unknown unit step backend")
    units = [clause for clause in formula.clauses if len(clause) == 1]
    if not units:
        return None
    unit_clause = sorted(units, key=lambda c: c.literals)[0]
    lit = unit_clause.literals[0]
    neg = -lit
    kept: list[Clause] = []
    removed: list[Clause] = []
    added: list[Clause] = []
    shortened: list[dict[str, Any]] = []
    for clause in formula.clauses:
        if lit in clause:
            removed.append(clause)
            continue
        if neg in clause:
            removed.append(clause)
            new_clause = Clause(x for x in clause if x != neg)
            added.append(new_clause)
            shortened.append({"from": clause.to_list(), "to": new_clause.to_list()})
            continue
        kept.append(clause)
    output = CNFFormula(kept + added)
    details = {
        "assigned_literal": lit,
        "unit_clause": unit_clause.to_list(),
        "satisfied_clauses": [clause.to_list() for clause in removed if lit in clause],
        "shortened_clauses": shortened,
        "conflict": output.contains_empty_clause,
    }
    return output, details


def _pure_literal_step(formula: CNFFormula, *,
                       backend: str = "python") -> tuple[CNFFormula, dict[str, Any]] | None:
    if backend == "rust":
        from witnora_ve import pure_step_native
        got = pure_step_native(formula.to_clause_lists())
        if got is None:
            return None
        output, lit, removed = got
        return CNFFormula(output), {
            "assigned_literal": lit,
            "removed_due_to_pure_literal": removed,
        }
    if backend != "python":
        raise ValueError("unknown pure step backend")
    signs: dict[int, set[int]] = {}
    for clause in formula.clauses:
        for lit in clause:
            signs.setdefault(abs(lit), set()).add(1 if lit > 0 else -1)
    pure_literals: list[int] = []
    for var, var_signs in signs.items():
        if var_signs == {1}:
            pure_literals.append(var)
        elif var_signs == {-1}:
            pure_literals.append(-var)
    if not pure_literals:
        return None
    lit = sorted(pure_literals, key=literal_sort_key)[0]
    removed = [clause for clause in formula.clauses if lit in clause]
    kept = [clause for clause in formula.clauses if lit not in clause]
    output = CNFFormula(kept)
    details = {
        "assigned_literal": lit,
        "removed_due_to_pure_literal": [clause.to_list() for clause in removed],
    }
    return output, details


def simplify(
    formula: CNFFormula,
    logger: StepLogger,
    *,
    log_component_decomposition: bool = True,
    backend: str = "python",
) -> tuple[CNFFormula, str]:
    """Apply S until fixed point or conflict.

    Returns ``(formula, status)`` where status is ``OK`` or ``UNSAT``.
    """

    if backend not in ("python", "rust"):
        raise ValueError("unknown simplifier backend")
    current = formula
    while True:
        if current.contains_empty_clause:
            return current, "UNSAT"

        unit = _unit_step(current, backend=backend)
        if unit is not None:
            output, details = unit
            removed = details["satisfied_clauses"] + [
                item["from"] for item in details["shortened_clauses"]
            ]
            added = [item["to"] for item in details["shortened_clauses"]]
            logger.append(
                "UP",
                current,
                output,
                details=details,
                removed_clauses=removed,
                added_clauses=added,
                assigned_literals=[details["assigned_literal"]],
                reconstruction_data={"assigned_literal": details["assigned_literal"]},
            )
            current = output
            continue

        pure = _pure_literal_step(current, backend=backend)
        if pure is not None:
            output, details = pure
            logger.append(
                "PLE",
                current,
                output,
                details=details,
                removed_clauses=details["removed_due_to_pure_literal"],
                assigned_literals=[details["assigned_literal"]],
                reconstruction_data={"assigned_literal": details["assigned_literal"]},
            )
            current = output
            continue

        subsumption = find_first_subsumption(current, backend=backend)
        if subsumption is not None:
            subsumer, removed_clause = subsumption
            output = current.without_clause(removed_clause)
            logger.append(
                "SUB",
                current,
                output,
                details={
                    "subsuming_clause": subsumer.to_list(),
                    "removed_clause": removed_clause.to_list(),
                },
                removed_clauses=[removed_clause.to_list()],
                reconstruction_data={"subsuming_clause": subsumer.to_list()},
            )
            current = output
            continue

        blocked = find_first_blocked_clause(current, backend=backend)
        if blocked is not None:
            removed_clause, proof = blocked
            output = current.without_clause(removed_clause)
            opposite = [
                clause.to_list()
                for clause in current.clauses
                if clause != removed_clause and -proof["blocked_literal"] in clause
            ]
            details = {
                "removed_clause": removed_clause.to_list(),
                "blocked_literal": proof["blocked_literal"],
                "checked_resolvents": proof["checked_resolvents"],
                "proof_digest": proof["proof_digest"],
                "opposite_clauses": opposite,
            }
            logger.append(
                "BCE",
                current,
                output,
                details=details,
                removed_clauses=[removed_clause.to_list()],
                reconstruction_data={
                    "removed_clause": removed_clause.to_list(),
                    "blocked_literal": proof["blocked_literal"],
                    "opposite_clauses": opposite,
                },
            )
            current = output
            continue

        details = component_details(current, backend=backend)
        if log_component_decomposition and details["component_count"] > 1:
            logger.append("CD", current, current, details=details)
        return current, "OK"
