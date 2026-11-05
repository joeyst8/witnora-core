"""Speculative two-ply resolution scheduling, outside the trusted Lean path.

Every transition is exact Davis-Putnam variable elimination and therefore
preserves SAT/UNSAT. Choosing the pivot by two-step lookahead is a heuristic,
not a new inference rule or a proved speed improvement.
"""
from __future__ import annotations

from .cnf import CNFFormula, resolvent
from .experimental_operator_search import structural_score


def elimination_options(formula: CNFFormula, *, max_pairs: int = 12,
                        growth_budget: int = 2) -> list[tuple[int, CNFFormula]]:
    """Enumerate bounded exact eliminations, including limited temporary growth."""
    options = []
    for pivot in formula.variables:
        pos = [row for row in formula.clauses if pivot in row]
        neg = [row for row in formula.clauses if -pivot in row]
        if len(pos) * len(neg) > max_pairs:
            continue
        rows = [row for row in formula.clauses if pivot not in row and -pivot not in row]
        for p in pos:
            for n in neg:
                candidate = resolvent(p, n, pivot)
                if candidate is not None:
                    rows.append(candidate)
        reduced = CNFFormula(rows)
        if (reduced != formula and
                reduced.num_clauses <= formula.num_clauses + growth_budget):
            options.append((pivot, reduced))
    return options


def two_ply_pivot(formula: CNFFormula, *, max_pairs: int = 12,
                  growth_budget: int = 2, beam_width: int = 8) -> CNFFormula:
    """Select the best measured structural outcome within two bounded pivots."""
    if max_pairs < 0 or growth_budget < 0 or not 1 <= beam_width <= 32:
        raise ValueError("invalid bounded lookahead budget")
    first = elimination_options(formula, max_pairs=max_pairs,
                                growth_budget=growth_budget)
    first.sort(key=lambda item: (
        -structural_score(formula, item[1]), item[1].num_clauses, item[0]))
    choices = [((), formula)]
    for pivot, reduced in first[:beam_width]:
        choices.append(((pivot,), reduced))
        for next_pivot, twice in elimination_options(
                reduced, max_pairs=max_pairs, growth_budget=growth_budget):
            choices.append(((pivot, next_pivot), twice))
    choices.sort(key=lambda item: (
        -structural_score(formula, item[1]),
        item[1].num_clauses, len(item[0]), item[0]))
    return choices[0][1]


def elimination_options_rust(formula: CNFFormula, *, max_pairs: int = 12,
                             growth_budget: int = 2) -> list[tuple[int, CNFFormula]]:
    """Opt-in native exact DP elimination options; original Python remains default."""
    from witnora_ve import elimination_options_native

    return [(pivot, CNFFormula.from_raw_clauses(rows))
            for pivot, rows in elimination_options_native(
                formula.to_clause_lists(), max_pairs, growth_budget)]


def two_ply_pivot_rust(formula: CNFFormula, *, max_pairs: int = 12,
                       growth_budget: int = 2, beam_width: int = 8) -> CNFFormula:
    """Opt-in native heuristic; SAT equisatisfiability is not a Lean proof."""
    from witnora_ve import two_ply_pivot_native

    return CNFFormula.from_raw_clauses(two_ply_pivot_native(
        formula.to_clause_lists(), max_pairs, growth_budget, beam_width))
