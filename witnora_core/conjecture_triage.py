"""Conservative triage of finite graph expression hypotheses.

Known identity catalog is incomplete and never establishes novelty by absence.
'Lean queue' means unproved proof obligations, not formal verification.
"""
from __future__ import annotations

from .expression_conjecture_search import expression_pool, run_expression_search
from .graph_conjecture_lab import graph_metrics, graphs


def normalize_expression(expr: str) -> str:
    """Canonicalize only safe syntactic arithmetic commutativity."""
    expr = expr.strip()
    for op in ("+", "*"):
        if expr.startswith("(") and expr.endswith(")") and expr.count(op) == 1:
            a, b = expr[1:-1].split(op)
            return "(" + op.join(sorted((a, b))) + ")"
    for op in ("min", "max"):
        if expr.startswith(op + "(") and expr.endswith(")"):
            a, b = expr[len(op) + 1:-1].split(",")
            return f"{op}({','.join(sorted((a, b)))})"
    return expr


def identity_key(statement: str) -> tuple[str, str]:
    left, right = statement.split(" = ", 1)
    return tuple(sorted((normalize_expression(left), normalize_expression(right))))


def known_identity_keys() -> set[tuple[str, str]]:
    catalog = {
        "n = (alpha+tau)",
        "alpha = (n-tau)",
        "tau = (n-alpha)",
        "chi = max(omega,chi)",
        "alpha = min(n,alpha)",
        "chi = min(n,chi)",
        "delta = min(n,delta)",
        "delta = min(m,delta)",
        "m = max(m,delta)",
        "m = max(m,nu)",
        "m = max(m,tau)",
    }
    for metric in ("alpha", "tau", "omega", "chi", "nu", "delta"):
        catalog.add(f"{metric} = min(n,{metric})")
        catalog.add(f"n = max(n,{metric})")
    return {identity_key(s) for s in catalog}


def expression_index():
    return {expression.label: expression for expression in expression_pool()}


def triage(*, adversarial_per_seed: int = 120) -> dict:
    if not 1 <= adversarial_per_seed <= 300:
        raise ValueError("bounded adversarial search only")
    base = run_expression_search()
    known = known_identity_keys()
    catalog_hits, unclassified, adversarially_falsified = [], [], []
    index = expression_index()
    adversarial = [(n, edges, graph_metrics(n, edges))
                   for n in (7, 8) for seed in (2107, 2239)
                   for _, edges in graphs(n, limit=adversarial_per_seed, seed=seed)]
    for title in base["holdout_survivors"]:
        if identity_key(title) in known:
            catalog_hits.append(title)
            continue
        left, right = title.split(" = ", 1)
        if left not in index or right not in index:
            raise ValueError("candidate absent from generated expression grammar")
        a, b = index[left], index[right]
        witness = next(((n, edges, a.evaluate(row), b.evaluate(row))
                        for n, edges, row in adversarial
                        if a.evaluate(row) != b.evaluate(row)), None)
        if witness is None:
            unclassified.append(title)
        else:
            n, edges, lhs, rhs = witness
            adversarially_falsified.append({
                "conjecture": title, "n": n,
                "edges": [list(edge) for edge in edges],
                "left_value": lhs, "right_value": rhs,
            })
    queue = [{
        "statement": name,
        "status": "PENDING_FORMALIZATION",
        "proof_obligations": [
            "Define graph invariants for arbitrary finite simple graphs in Lean",
            "Prove the universally quantified equality or produce counterexample",
            "Check any proof with the Lean kernel",
            "Complete independent prior-art and novelty review",
        ],
        "lean_verified": False,
        "novelty_verified": False,
    } for name in sorted(unclassified)[:10]]
    return {
        "original_survivors": len(base["holdout_survivors"]),
        "catalog_known_identity_matches": sorted(catalog_hits),
        "adversarial_graphs": len(adversarial),
        "adversarially_falsified": adversarially_falsified,
        "unclassified_survivors": sorted(unclassified),
        "lean_review_queue": queue,
        "known_identity_catalog_complete": False,
        "lean_verified": False,
        "novelty_verified": False,
        "theorem_proven": False,
        "promoted": False,
    }
