"""Experimental graph-invariant-driven variable-elimination policy invention.

These policies are hypotheses about elimination order, not new logical
inference rules. Each step is exact Davis-Putnam resolution, with bounded
growth and no trusted certificate status.
"""
from __future__ import annotations

from itertools import combinations

from .cnf import CNFFormula, resolvent
from .spoke_discovery import extract_binary_xor_equations


POLICIES = ("min_fill", "xor_boundary", "max_release")


def graph_invariants(formula: CNFFormula) -> dict:
    neighbors = {v: set() for v in formula.variables}
    for clause in formula.clauses:
        variables = sorted(set(clause.variables))
        for a, b in combinations(variables, 2):
            neighbors[a].add(b)
            neighbors[b].add(a)
    xor_degree = {v: 0 for v in formula.variables}
    for u, v, _ in extract_binary_xor_equations(formula):
        xor_degree[u] += 1
        xor_degree[v] += 1
    fill = {}
    for v, adjacent in neighbors.items():
        missing = sum(b not in neighbors[a] for a, b in combinations(sorted(adjacent), 2))
        fill[v] = missing
    return {
        "degree": {v: len(adjacent) for v, adjacent in neighbors.items()},
        "fill": fill,
        "xor_degree": xor_degree,
    }


def eliminate_with_policy(formula: CNFFormula, policy: str, *,
                          max_pairs: int = 12, max_clause_growth: int = 2) -> CNFFormula:
    if policy not in POLICIES:
        raise ValueError("unknown invariant-guided elimination policy")
    invariants = graph_invariants(formula)
    choices = []
    for v in formula.variables:
        pos = [clause for clause in formula.clauses if v in clause]
        neg = [clause for clause in formula.clauses if -v in clause]
        if len(pos) * len(neg) > max_pairs:
            continue
        rows = [clause for clause in formula.clauses if v not in clause and -v not in clause]
        for p in pos:
            for n in neg:
                resolved = resolvent(p, n, v)
                if resolved is not None:
                    rows.append(resolved)
        reduced = CNFFormula(rows)
        if reduced == formula or reduced.num_clauses > formula.num_clauses + max_clause_growth:
            continue
        stats = invariants
        if policy == "min_fill":
            priority = (stats["fill"][v], stats["degree"][v], reduced.num_clauses)
        elif policy == "xor_boundary":
            # Prefer eliminating non-XOR variables; protect densely
            # constrained parity backbones from premature destruction.
            priority = (stats["xor_degree"][v], stats["fill"][v], reduced.num_clauses)
        else:
            priority = (reduced.num_clauses - formula.num_clauses,
                        stats["fill"][v], stats["degree"][v])
        choices.append((priority, v, reduced))
    if not choices:
        return formula
    _, _, best = min(choices, key=lambda item: (item[0], item[1]))
    return best


def min_fill_elimination(formula: CNFFormula) -> CNFFormula:
    return eliminate_with_policy(formula, "min_fill")


def xor_boundary_elimination(formula: CNFFormula) -> CNFFormula:
    return eliminate_with_policy(formula, "xor_boundary")


def max_release_elimination(formula: CNFFormula) -> CNFFormula:
    return eliminate_with_policy(formula, "max_release")
