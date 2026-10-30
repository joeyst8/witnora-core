"""Experimental bounded 1..3 variable separators between exact parity equations.

Purely observational. A parity-incidence cut is NOT a certified separator of
the complete CNF; non-XOR clauses may reconnect the components.
"""
from __future__ import annotations

from itertools import combinations

from .cnf import CNFFormula
from .parity_separator_fingerprint import _components
from .xor import detect_cnf_xor_patterns


def bounded_parity_separators(formula: CNFFormula, *, max_cut: int = 3,
                             max_shared: int = 18,
                             max_trials: int = 2000) -> dict:
    if not 1 <= max_cut <= 3 or max_shared < 1 or max_trials < 1:
        raise ValueError("invalid bounded separator search")
    equations = sorted(detect_cnf_xor_patterns(formula, max_k=6).equations,
                       key=lambda e: (e.variables, e.rhs))
    supports = [set(eq.variables) for eq in equations]
    baseline = len(_components(supports))
    occurrence = {v: sum(v in s for s in supports)
                  for v in sorted(set().union(*supports) if supports else set())}
    shared = sorted((v for v, n in occurrence.items() if n >= 2),
                    key=lambda v: (-occurrence[v], v))[:max_shared]
    found = []
    trials = 0
    exhausted = False
    for size in range(1, max_cut + 1):
        for cut in combinations(sorted(shared), size):
            if trials >= max_trials:
                exhausted = True
                break
            trials += 1
            if any(set(previous["variables"]).issubset(cut) for previous in found):
                continue
            reduced = [support.difference(cut) for support in supports]
            groups = _components(reduced)
            if len(groups) <= baseline:
                continue
            if any(not set().union(*(reduced[i] for i in group))
                   for group in groups):
                continue
            found.append({
                "variables": list(cut), "size": size,
                "components_before": baseline,
                "components_after": len(groups),
                "component_equation_indices": groups,
            })
        if exhausted:
            break
    return {
        "source_sha256": formula.formula_hash,
        "exact_parity_equations": len(equations),
        "candidate_cuts": found,
        "candidate_count": len(found),
        "smallest_cut_size": min((x["size"] for x in found), default=None),
        "shared_variables_considered": len(shared),
        "trials": trials,
        "budget_exhausted": exhausted,
        "full_cnf_separation_verified": False,
        "cnf_transformed": False,
        "lean_verified": False, "novelty_verified": False, "promoted": False,
    }
