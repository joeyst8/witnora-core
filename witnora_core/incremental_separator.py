"""Experimental cheap exact-XOR screen and cached full-CNF separator plan.

Cache is in-process and keyed by immutable CNFFormula. It cannot improve first
encounters, must not bypass full-CNF cut audit, and is not a trusted proof.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import product

from .cnf import CNFFormula
from .multicut_parity_separator import bounded_parity_separators
from .separator_conditioned_solve import primal_components, restrict_formula, split_residual


def possible_two_xor_patterns(formula: CNFFormula) -> bool:
    """Necessary cheap screen for 2+ exact arity-2..6 XOR encodings."""
    groups: dict[tuple[int, ...], int] = {}
    for clause in formula.clauses:
        support = tuple(sorted({abs(lit) for lit in clause}))
        if 2 <= len(support) <= 6 and len(support) == len(clause):
            groups[support] = groups.get(support, 0) + 1
    return sum(n == 1 << (len(support) - 1)
               for support, n in groups.items()) >= 2


@lru_cache(maxsize=128)
def cached_full_cut(formula: CNFFormula) -> tuple[int, ...] | None:
    if not possible_two_xor_patterns(formula):
        return None
    original_count = len(primal_components(formula))
    for row in bounded_parity_separators(formula)["candidate_cuts"]:
        cut = tuple(row["variables"])
        if len(primal_components(formula, cut)) > original_count:
            return cut
    return None


def solve_incremental(formula: CNFFormula) -> dict:
    from pysat.solvers import Glucose3

    def sat(candidate):
        with Glucose3(bootstrap_with=candidate.to_clause_lists()) as solver:
            return bool(solver.solve())

    cut = cached_full_cut(formula)
    if cut is None:
        return {"satisfiable": sat(formula), "mode": "direct_fallback",
                "cut": [], "component_calls": 0,
                "lean_verified": False, "promoted": False}
    calls = 0
    for values in product((False, True), repeat=len(cut)):
        residual = restrict_formula(formula, dict(zip(cut, values)))
        if residual.contains_empty_clause:
            continue
        good = True
        for component in split_residual(residual):
            calls += 1
            if not sat(component):
                good = False
                break
        if good:
            return {"satisfiable": True, "mode": "conditioned",
                    "cut": list(cut), "component_calls": calls,
                    "lean_verified": False, "promoted": False}
    return {"satisfiable": False, "mode": "conditioned",
            "cut": list(cut), "component_calls": calls,
            "lean_verified": False, "promoted": False}
