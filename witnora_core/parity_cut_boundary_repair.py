"""Experimental parity-cut boundary repair against the full CNF graph.

A parity-equation separator may be invalidated by non-XOR clauses. Given
a proposed cut and two anchors, search for the smallest additional set
of variables restoring separation. This is bounded vertex-cut search,
not a novel complexity result or a verified inference rule.
"""
from __future__ import annotations

from itertools import combinations
from typing import Any

from .cnf import CNFFormula
from .hidden_separator_challenge import full_cnf_anchors_separated


def _valid_variables(formula: CNFFormula, cut: tuple[int, ...],
                     left: int, right: int) -> bool:
    variables = set(formula.variables)
    return (left != right and left in variables and right in variables
            and left not in cut and right not in cut
            and len(set(cut)) == len(cut)
            and all(v in variables for v in cut))


def repair_parity_separator(
    formula: CNFFormula,
    parity_cut: tuple[int, ...],
    left_anchor: int,
    right_anchor: int,
    *,
    max_extra: int = 2,
    max_trials: int = 10000,
) -> dict[str, Any]:
    """Return a fully audited augmented cut or fail closed.

    The input cut is a candidate, not sound evidence about the CNF.
    Only full-CNF reachability audits authorize a separated=True result.
    """
    if not 0 <= max_extra <= 3 or max_trials < 1:
        raise ValueError("invalid bounded search parameters")
    original = tuple(sorted(parity_cut))
    if not _valid_variables(formula, original, left_anchor, right_anchor):
        raise ValueError("invalid candidate or anchors")
    available = sorted(set(formula.variables) -
                       set(original) - {left_anchor, right_anchor})
    trials = 0
    for size in range(max_extra + 1):
        for extra in combinations(available, size):
            if trials >= max_trials:
                return {
                    "status": "BUDGET_EXHAUSTED",
                    "parity_cut": list(original),
                    "repaired_cut": None,
                    "extra_variables": None,
                    "trials": trials,
                    "full_cnf_separated": False,
                }
            trials += 1
            cut = tuple(sorted((*original, *extra)))
            if full_cnf_anchors_separated(
                    formula, cut, left_anchor, right_anchor):
                return {
                    "status": "REPAIRED" if extra else "ALREADY_SOUND",
                    "parity_cut": list(original),
                    "repaired_cut": list(cut),
                    "extra_variables": list(extra),
                    "trials": trials,
                    "full_cnf_separated": True,
                }
    return {
        "status": "NO_REPAIR_WITHIN_BUDGET",
        "parity_cut": list(original),
        "repaired_cut": None,
        "extra_variables": None,
        "trials": trials,
        "full_cnf_separated": False,
    }


def independent_minimum_anchor_cut(
    formula: CNFFormula, left_anchor: int, right_anchor: int,
    *, max_size: int = 5,
) -> tuple[int, ...] | None:
    """Exhaustive reference unconstrained by the parity candidate."""
    if max_size < 0:
        raise ValueError("negative max_size")
    variables = sorted(set(formula.variables) - {left_anchor, right_anchor})
    for size in range(min(max_size, len(variables)) + 1):
        for cut in combinations(variables, size):
            if full_cnf_anchors_separated(formula, cut, left_anchor, right_anchor):
                return cut
    return None
