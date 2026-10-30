"""Cheap pre-search gate for adaptive SAT elimination (experimental only)."""
from __future__ import annotations

from .adaptive_lookahead_prototype import adaptive_pivot
from .cnf import CNFFormula
from .experimental_operator_search import bounded_elimination


def cheap_pivot_features(formula: CNFFormula, *, max_pairs: int = 12) -> dict:
    """Count bounded mixed-polarity candidate pivots without constructing resolvents."""
    occurrence: dict[int, list[int]] = {}
    for clause in formula.clauses:
        for lit in clause:
            counts = occurrence.setdefault(abs(lit), [0, 0])
            counts[0 if lit > 0 else 1] += 1
    viable = sum(1 for pos, neg in occurrence.values()
                 if pos and neg and pos * neg <= max_pairs)
    free = sum(1 for pos, neg in occurrence.values() if not (pos and neg))
    return {"viable_mixed_pivots": viable, "pure_pivots": free,
            "variables": formula.num_vars, "clauses": formula.num_clauses}


def selective_pivot(formula: CNFFormula, *, max_pairs: int = 12,
                    min_mixed_pivots: int = 3, max_vars: int = 25,
                    max_clauses: int = 140, expansion_budget: int = 24
                    ) -> tuple[CNFFormula, dict]:
    """Choose greedy for low-opportunity/large cases and bounded adaptive otherwise.

    No learned prediction or general speed guarantee is claimed. Parameters are
    fixed before fresh-seed comparison and all outputs remain untrusted.
    """
    if (max_pairs < 0 or min_mixed_pivots < 1 or max_vars < 1
            or max_clauses < 1 or expansion_budget < 1):
        raise ValueError("invalid selective lookahead gate")
    features = cheap_pivot_features(formula, max_pairs=max_pairs)
    eligible = (features["viable_mixed_pivots"] >= min_mixed_pivots
                and features["variables"] <= max_vars
                and features["clauses"] <= max_clauses)
    if eligible:
        candidate, details = adaptive_pivot(
            formula, max_pairs=max_pairs, expansion_budget=expansion_budget)
        return candidate, {**features, "mode": "adaptive",
                           "expanded": details["expanded"],
                           "trusted": False, "promoted": False}
    greedy = bounded_elimination(bounded_elimination(formula, max_pairs=max_pairs),
                                 max_pairs=max_pairs)
    return greedy, {**features, "mode": "greedy",
                    "expanded": 0, "trusted": False, "promoted": False}
