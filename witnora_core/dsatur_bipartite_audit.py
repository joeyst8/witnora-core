"""Independent finite audit of DSATUR optimality on bipartite graphs.

Brélaz's known theorem says DSATUR is optimal on bipartite graphs.
This is an implementation audit, not a newly discovered theorem or Lean proof.
"""
from __future__ import annotations

from itertools import combinations
import random

from .graph_conjecture_lab import graphs
from .nonedge_matching_bound import _dsatur_greedy_coloring


def bipartition(n: int, edges: tuple[tuple[int, int], ...]) -> list[int] | None:
    adjacency = [set() for _ in range(n)]
    for u, v in edges:
        adjacency[u].add(v)
        adjacency[v].add(u)
    parts = [-1] * n
    for root in range(n):
        if parts[root] >= 0:
            continue
        parts[root] = 0
        queue = [root]
        for u in queue:
            for v in sorted(adjacency[u]):
                if parts[v] < 0:
                    parts[v] = 1 - parts[u]
                    queue.append(v)
                elif parts[v] == parts[u]:
                    return None
    assert all(parts[u] != parts[v] for u, v in edges)
    return parts


def bipartition_rust(n: int, edges: tuple[tuple[int, int], ...]) -> list[int] | None:
    """Opt-in native BFS partition check; Python remains the audit default."""
    from witnora_ve import bipartition_audit_native
    if n < 0 or n > 4096:
        raise ValueError("vertex budget exceeded")
    return bipartition_audit_native(n, list(edges))


def run_bipartite_audit() -> dict:
    stats = {"exhaustive_graphs": 0, "exhaustive_bipartite": 0,
             "random_bipartite": 0, "dsatur_violations": 0,
             "dsatur_three_color_bipartite": 0}
    examples = {"first_violation": None}
    def check(label: str, n: int, edges: tuple[tuple[int, int], ...]):
        parts = bipartition(n, edges)
        if parts is None:
            return
        actual = (2 if edges else 1) if n else 0
        found = _dsatur_greedy_coloring(n, edges)
        if found["bound"] != actual:
            stats["dsatur_violations"] += 1
            if examples["first_violation"] is None:
                examples["first_violation"] = {
                    "family": label, "n": n, "edges": [list(e) for e in edges],
                    "bipartition": parts, "expected": actual,
                    "dsatur": found,
                }
        stats["dsatur_three_color_bipartite"] += found["bound"] >= 3

    for n in range(1, 7):
        for _, edges in graphs(n):
            stats["exhaustive_graphs"] += 1
            if bipartition(n, edges) is not None:
                stats["exhaustive_bipartite"] += 1
                check("exhaustive", n, edges)
    rng = random.Random(20261103)
    for n in (8, 12, 16):
        for index in range(1200):
            left = 1 + index % (n - 1)
            p = (0.08, 0.30, 0.50, 0.75, 0.95)[index % 5]
            labels = list(range(n))
            rng.shuffle(labels)
            a, b = labels[:left], labels[left:]
            edges = tuple(sorted((min(u, v), max(u, v)) for u in a for v in b
                                 if rng.random() < p))
            assert bipartition(n, edges) is not None
            stats["random_bipartite"] += 1
            check("random_bipartite", n, edges)
    return {"statistics": stats, "examples": examples,
            "literature_known_theorem": True,
            "lean_verified": False, "novelty_verified": False,
            "promoted": False}
