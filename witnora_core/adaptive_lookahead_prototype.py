"""Budgeted adaptive elimination search; experimental, not a trusted proof.

Every candidate uses exact Davis-Putnam elimination from lookahead_pivot_prototype.
This module only chooses an elimination order. No performance or novelty claim.
"""
from __future__ import annotations

from .cnf import CNFFormula
from .experimental_operator_search import bounded_elimination, structural_score
from .lookahead_pivot_prototype import elimination_options


def adaptive_pivot(formula: CNFFormula, *, max_pairs: int = 12,
                   growth_budget: int = 2, beam_width: int = 4,
                   expansion_budget: int = 48, max_depth: int = 3,
                   ambiguity_margin: float = 2.0) -> tuple[CNFFormula, dict]:
    """Return the best structurally ranked state, guarding against greedy regression.

    A clear profitable first pivot skips speculation. Ambiguous situations use
    a capped beam. A third ply is considered only when two plies have failed
    to beat the greedy baseline. Runtime gains are empirical, not guaranteed.
    """
    if (max_pairs < 0 or growth_budget < 0 or not 1 <= beam_width <= 32
            or not 1 <= expansion_budget <= 1000 or max_depth not in (2, 3)
            or ambiguity_margin < 0):
        raise ValueError("invalid adaptive lookahead budget")
    greedy = bounded_elimination(bounded_elimination(formula, max_pairs=max_pairs),
                                 max_pairs=max_pairs)
    score = lambda f: structural_score(formula, f)
    best = greedy if score(greedy) > 0 else formula
    options = elimination_options(formula, max_pairs=max_pairs,
                                  growth_budget=growth_budget)
    options.sort(key=lambda item: (-score(item[1]), item[1].num_clauses,
                                   item[0], item[1].formula_hash))
    if not options:
        return best, {"mode": "no_pivots", "expanded": 0, "depth": 0,
                      "baseline_score": score(greedy), "candidate_score": score(best),
                      "trusted": False, "promoted": False}
    if (score(options[0][1]) > 0 and
            (len(options) == 1 or
             score(options[0][1]) - score(options[1][1]) >= ambiguity_margin)):
        return best, {"mode": "greedy_confident", "expanded": 0, "depth": 0,
                      "baseline_score": score(greedy), "candidate_score": score(best),
                      "trusted": False, "promoted": False}

    frontier = [(tuple([pivot]), reduced) for pivot, reduced in options[:beam_width]]
    seen = {formula.formula_hash}
    expanded = 0
    depth_reached = 0
    for depth in range(1, max_depth + 1):
        if not frontier or expanded >= expansion_budget:
            break
        next_frontier = []
        for path, state in frontier:
            if state.formula_hash in seen:
                continue
            seen.add(state.formula_hash)
            expanded += 1
            if (score(state), -len(path), state.formula_hash) > (
                    score(best), 0, best.formula_hash):
                best = state
            depth_reached = max(depth_reached, depth)
            if expanded >= expansion_budget:
                break
            if depth < max_depth:
                for pivot, reduced in elimination_options(
                        state, max_pairs=max_pairs, growth_budget=growth_budget):
                    next_frontier.append((path + (pivot,), reduced))
        if depth == 2 and score(best) > score(greedy):
            break
        next_frontier.sort(key=lambda item: (
            -score(item[1]), len(item[0]), item[0], item[1].formula_hash))
        frontier = next_frontier[:beam_width]
    return best, {"mode": "adaptive_search", "expanded": expanded,
                  "depth": depth_reached, "baseline_score": score(greedy),
                  "candidate_score": score(best), "trusted": False,
                  "promoted": False}
