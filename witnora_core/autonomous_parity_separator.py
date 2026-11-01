"""Autonomous parity candidate discovery and full-CNF component repair.

No hidden-generator boundary or anchor metadata is supplied to this
algorithm. Exact XOR patterns provide initial component groups. Every
accepted augmented cut must separate the entire equation groups in the
full CNF primal graph, including non-XOR clauses.
"""
from __future__ import annotations

from itertools import combinations

from .cnf import CNFFormula
from .multicut_parity_separator import bounded_parity_separators
from .xor import detect_cnf_xor_patterns


def _cnf_component_labels(formula: CNFFormula, removed: set[int]):
    """Independent whole-CNF graph traversal after removing cut variables."""
    graph = {v: set() for v in formula.variables if v not in removed}
    for clause in formula.clauses:
        variables = set(clause.variables) - removed
        for u in variables:
            graph[u].update(variables - {u})
    labels = {}
    component_id = 0
    for start in sorted(graph):
        if start in labels:
            continue
        component_id += 1
        stack = [start]
        labels[start] = component_id
        while stack:
            u = stack.pop()
            for v in sorted(graph[u]):
                if v not in labels:
                    labels[v] = component_id
                    stack.append(v)
    return labels


def full_cnf_groups_separated(formula: CNFFormula,
                              cut: tuple[int, ...],
                              groups: list[set[int]]) -> bool:
    """Require each parity group to survive and no full-CNF component
    to contain variables from two distinct groups."""
    labels = _cnf_component_labels(formula, set(cut))
    occupied = []
    for group in groups:
        remaining = group - set(cut)
        if not remaining:
            return False
        occupied.append({labels[v] for v in remaining})
    return all(not left.intersection(right)
               for i, left in enumerate(occupied)
               for right in occupied[i + 1:])


def discover_repaired_separator(
    formula: CNFFormula, *,
    max_cut: int = 3, max_extra: int = 2,
    max_candidates: int = 10, max_trials: int = 10000,
):
    if not 1 <= max_cut <= 3 or not 0 <= max_extra <= 3:
        raise ValueError("invalid search width")
    if max_candidates < 1 or max_trials < 1:
        raise ValueError("invalid work budget")
    detected = bounded_parity_separators(
        formula, max_cut=max_cut, max_trials=max_trials)
    equations = sorted(
        detect_cnf_xor_patterns(formula, max_k=6).equations,
        key=lambda eq: (eq.variables, eq.rhs))
    supports = [set(eq.variables) for eq in equations]
    trials = 0
    candidate_count = len(detected["candidate_cuts"])
    winners = []
    for candidate in detected["candidate_cuts"][:max_candidates]:
        parity_cut = tuple(candidate["variables"])
        groups = [
            set().union(*(supports[i] for i in indices))
            for indices in candidate["component_equation_indices"]
        ]
        if len(groups) < 2:
            continue
        available = sorted(set(formula.variables) - set(parity_cut))
        found = None
        for width in range(max_extra + 1):
            for extra in combinations(available, width):
                if trials >= max_trials:
                    return {
                        "status": "BUDGET_EXHAUSTED",
                        "candidate_count": candidate_count,
                        "trials": trials, "cut": None,
                        "full_cnf_groups_separated": False,
                    }
                trials += 1
                cut = tuple(sorted((*parity_cut, *extra)))
                if full_cnf_groups_separated(formula, cut, groups):
                    found = {
                        "cut": list(cut),
                        "parity_cut": list(parity_cut),
                        "extra": list(extra),
                        "parity_component_count": len(groups),
                        "full_cnf_groups_separated": True,
                    }
                    break
            if found is not None:
                break
        if found is not None:
            winners.append(found)
    if not winners:
        return {
            "status": "NO_AUDITED_CANDIDATE",
            "candidate_count": candidate_count,
            "trials": trials, "cut": None,
            "full_cnf_groups_separated": False,
        }
    best = min(winners, key=lambda w: (
        len(w["cut"]), len(w["extra"]), tuple(w["cut"])))
    return {
        "status": "FOUND",
        "candidate_count": candidate_count,
        "trials": trials,
        **best,
    }
