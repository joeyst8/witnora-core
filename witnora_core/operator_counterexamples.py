"""Greedy shrinking of counterexamples to experimental operator hypotheses.

A counterexample can disprove a predicted structural improvement. It is not
automatically a counterexample to SAT soundness; the distinction is explicit.
"""
from __future__ import annotations

from collections.abc import Callable

from .cnf import CNFFormula
from .experimental_operator_search import (
    OPERATORS, TRANSFORMS, structural_score,
)


def apply_sequence(formula: CNFFormula, sequence: tuple[str, ...]) -> CNFFormula:
    current = formula
    for name in sequence:
        if name not in TRANSFORMS:
            raise ValueError("unknown experimental operator")
        current = TRANSFORMS[name](current)
    return current


def interaction_gain(formula: CNFFormula, sequence: tuple[str, ...]) -> float:
    if not sequence:
        raise ValueError("empty sequence")
    combined = structural_score(formula, apply_sequence(formula, sequence))
    best_single = max(
        structural_score(formula, TRANSFORMS[name](formula))
        for name in OPERATORS
    )
    return combined - best_single


def minimize_counterexample(
    formula: CNFFormula, predicate: Callable[[CNFFormula], bool], *,
    min_clauses: int = 3, min_variables: int = 3,
    max_checks: int = 400,
) -> CNFFormula:
    if not predicate(formula):
        raise ValueError("input does not exhibit the requested failure")
    current = formula
    checks = 0
    while checks < max_checks:
        removed = False
        for clause in current.clauses:
            if checks >= max_checks:
                break
            smaller = current.without_clause(clause)
            if (smaller.num_clauses < min_clauses or
                    smaller.num_vars < min_variables):
                continue
            checks += 1
            if predicate(smaller):
                current = smaller
                removed = True
                break
        if not removed:
            break
    return current
