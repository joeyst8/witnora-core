"""Targeted empirical falsification of two maximum/chromatic conjectures.

Finite evidence is not a proof; 'no counterexample' is not novelty evidence.
"""
from __future__ import annotations

from itertools import combinations

from .graph_conjecture_lab import graph_metrics, graphs


def cycle(n):
    return (n, tuple(sorted({tuple(sorted((i, (i + 1) % n)))
                             for i in range(n)})))


def wheel(n):
    base_n, edges = cycle(n - 1)
    return n, tuple(sorted(set(edges) | {(i, n - 1) for i in range(base_n)}))


def complete_bipartite(a, b):
    return a + b, tuple((u, a + v) for u in range(a) for v in range(b))


def mycielski_c5():
    # Mycielskian of C5: 11 vertices, triangle-free, chromatic number 4.
    _, base = cycle(5)
    edges = set(base)
    for u, v in base:
        edges.add((min(u, 5 + v), max(u, 5 + v)))
        edges.add((min(v, 5 + u), max(v, 5 + u)))
    for i in range(5):
        edges.add((5 + i, 10))
    return 11, tuple(sorted(edges))


def special_graphs():
    for n in range(1, 12):
        yield f"complete_{n}", n, tuple(combinations(range(n), 2))
    for n in range(3, 12):
        size, edges = cycle(n)
        yield f"cycle_{n}", size, edges
    for n in range(4, 12):
        size, edges = wheel(n)
        yield f"wheel_{n}", size, edges
    for a in range(1, 6):
        for b in range(1, 6):
            n, edges = complete_bipartite(a, b)
            yield f"K_{a}_{b}", n, edges
    n, edges = mycielski_c5()
    yield "mycielski_C5", n, edges


def evaluate(n, edges):
    m = graph_metrics(n, edges)
    first = max(m["m"], m["omega"]) == max(m["m"], m["chi"])
    second = max(m["tau"], m["omega"]) == max(m["tau"], m["chi"])
    return first, second, m


def challenge(*, random_each: int = 120):
    if not 1 <= random_each <= 300:
        raise ValueError("bounded research challenge")
    cases = list(special_graphs())
    for n in (8, 9, 10, 11):
        for seed in (2741, 2857):
            for _, edges in graphs(n, limit=random_each, seed=seed):
                cases.append((f"random_n{n}_seed{seed}", n, edges))
    failure = [[], []]
    for label, n, edges in cases:
        a, b, metric = evaluate(n, edges)
        for index, valid in enumerate((a, b)):
            if not valid:
                failure[index].append({
                    "family": label, "n": n,
                    "edges": [list(edge) for edge in edges], "metrics": metric,
                })
    return {
        "cases": len(cases),
        "first_conjecture": "max(m,omega)=max(m,chi)",
        "second_conjecture": "max(tau,omega)=max(tau,chi)",
        "first_counterexamples": failure[0],
        "second_counterexamples": failure[1],
        "proof_obligations": [
            "For finite simple G prove chi(G) <= max(edges(G), cliqueNumber(G))",
            "For finite simple G prove chi(G) <= max(vertexCoverNumber(G), cliqueNumber(G))",
            "Derive max equalities using omega(G) <= chi(G)",
            "Review existing graph-theoretic results for prior art",
        ],
        "lean_status": "NOT_FORMALIZED",
        "lean_verified": False, "novelty_verified": False,
        "theorem_proven": False, "promoted": False,
    }
