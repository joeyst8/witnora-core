"""Experimental exact-parity and shared-variable separator fingerprint.

Observational only: no CNF rewriting, SAT conclusion, novelty, or Lean status.
Exact XOR-pattern detection is reused from existing conservative infrastructure.
"""
from __future__ import annotations

from .cnf import CNFFormula
from .xor import detect_cnf_xor_patterns


def _components(supports: list[set[int]]) -> list[list[int]]:
    remaining = set(range(len(supports)))
    groups = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        group = [start]
        queue = [start]
        while queue:
            current = queue.pop()
            adjacent = sorted(i for i in remaining if supports[current] & supports[i])
            for index in adjacent:
                remaining.remove(index)
                group.append(index)
                queue.append(index)
        groups.append(sorted(group))
    return groups


def parity_separator_fingerprint(formula: CNFFormula, *, max_k: int = 6) -> dict:
    """Find a single variable whose removal separates the parity-equation graph.

    This is a candidate *structural* separator, not a claim that the complete
    CNF decomposes after conditioning on that variable. Non-XOR clauses may
    cross the candidate boundary and must be audited before any solving use.
    """
    if not 2 <= max_k <= 6:
        raise ValueError("bounded XOR detection requires arity 2..6")
    system = detect_cnf_xor_patterns(formula, max_k=max_k)
    equations = sorted(system.equations, key=lambda e: (e.variables, e.rhs))
    supports = [set(e.variables) for e in equations]
    base = _components(supports)
    candidates = []
    for variable in sorted(set().union(*supports) if supports else set()):
        incidence = sum(variable in support for support in supports)
        if incidence < 2:
            continue
        reduced = [support - {variable} for support in supports]
        after = _components(reduced)
        if len(after) > len(base):
            candidates.append({
                "variable": variable,
                "parity_equations_incident": incidence,
                "components_before": len(base),
                "components_after": len(after),
                "component_equation_indices": after,
            })
    return {
        "source_sha256": formula.formula_hash,
        "exact_parity_equations": len(equations),
        "parity_equation_supports": [list(e.variables) for e in equations],
        "separator_candidates": candidates,
        "candidate_count": len(candidates),
        "non_xor_cross_edges_audited": False,
        "cnf_transformed": False,
        "lean_verified": False,
        "novelty_verified": False,
        "promoted": False,
    }
