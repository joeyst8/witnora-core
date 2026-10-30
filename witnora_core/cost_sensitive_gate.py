"""Experimental cost-sensitive selection of greedy versus adaptive elimination.

The threshold is trained only on separate cases. No novelty or speed claim.
"""
from __future__ import annotations

from .adaptive_lookahead_prototype import adaptive_pivot
from .cnf import CNFFormula
from .experimental_operator_search import bounded_elimination
from .selective_lookahead_prototype import cheap_pivot_features

THRESHOLDS = (2, 3, 5, 8, 1000000)


def choose_threshold(observations: list[dict], *, cost_weight: float = 2.0
                     ) -> dict:
    """Fit five prespecified decision stumps on paired training measurements.

    Reward = extra structural score minus cost_weight * extra milliseconds.
    Favor simpler (higher threshold) on ties. 1000000 means always greedy.
    """
    if not observations or cost_weight < 0:
        raise ValueError("missing observations or invalid penalty")
    best = None
    for threshold in THRESHOLDS:
        utility = 0.0
        selections = 0
        for row in observations:
            if row["mixed_pivots"] >= threshold and row["variables"] <= 25 and row["clauses"] <= 140:
                selections += 1
                utility += (row["adaptive_score"] - row["greedy_score"]
                            - cost_weight * (row["adaptive_ms"] - row["greedy_ms"]))
        candidate = (round(utility, 8), threshold)
        if best is None or candidate > best:
            best = candidate
            winning = (threshold, selections)
    return {"threshold": winning[0], "train_utility": best[0],
            "selected_train_cases": winning[1], "train_cases": len(observations),
            "cost_weight": cost_weight, "novelty_verified": False, "promoted": False}


def cost_sensitive_pivot(formula: CNFFormula, *, threshold: int,
                         max_pairs: int = 12) -> tuple[CNFFormula, dict]:
    """Apply a frozen learned threshold, never refit at inference time."""
    if threshold not in THRESHOLDS or max_pairs < 0:
        raise ValueError("threshold must come from the preregistered set")
    features = cheap_pivot_features(formula, max_pairs=max_pairs)
    use_adaptive = (features["viable_mixed_pivots"] >= threshold
                    and features["variables"] <= 25
                    and features["clauses"] <= 140)
    if use_adaptive:
        candidate, details = adaptive_pivot(
            formula, max_pairs=max_pairs, expansion_budget=24)
        expanded = details["expanded"]
    else:
        candidate = bounded_elimination(
            bounded_elimination(formula, max_pairs=max_pairs), max_pairs=max_pairs)
        expanded = 0
    return candidate, {**features, "mode": "adaptive" if use_adaptive else "greedy",
                       "expanded": expanded, "threshold": threshold,
                       "lean_verified": False, "promoted": False}
