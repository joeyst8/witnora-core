"""Structured out-of-distribution coloring benchmark, without exact-oracle gating.

Unlike the earlier conditional repair studies, all heuristics run on every
graph as an ordinary pipeline; exact k-colorability is used only afterward
to score the resulting colorings.
"""
from __future__ import annotations

from itertools import combinations
from time import perf_counter
import random

from .color_repair_lab import multistart_dsatur, bounded_recolor, _checked
from .double_kempe_lab import double_kempe_repair
from .dsatur_adversarial_lab import exact_k_coloring
from .kempe_repair_lab import kempe_repair
from .nonedge_matching_bound import _dsatur_greedy_coloring


def _edges_from_set(edges: set[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return tuple(sorted((min(u, v), max(u, v)) for u, v in edges if u != v))


def structured_graphs(seed: int = 20261102, per_family: int = 60):
    rng = random.Random(seed)
    for index in range(per_family):
        n = (12, 14, 16)[index % 3]

        # 1. Planted 3/4-partition graphs: guaranteed k-colorable, but with
        # variable within-class structure and cross-class densities.
        k = 3 + index % 2
        classes = list(range(k)) + [rng.randrange(k) for _ in range(n - k)]
        rng.shuffle(classes)
        p = (0.35, 0.65, 0.85)[index % 3]
        edges = {(u, v) for u, v in combinations(range(n), 2)
                 if classes[u] != classes[v] and rng.random() < p}
        yield "planted_coloring", n, _edges_from_set(edges)

        # 2. Bipartite graphs, including deliberately unbalanced sides.
        left_size = (2, 5, 8)[index % 3]
        p = (0.2, 0.5, 0.8)[index % 3]
        edges = {(u, v) for u in range(left_size) for v in range(left_size, n)
                 if rng.random() < p}
        yield "bipartite", n, _edges_from_set(edges)

        # 3. Circulant constructions, with several chord lengths; these
        # contain highly symmetric cycles and denser regular graphs.
        steps = {(1 + index % (n // 2))}
        if index % 2:
            steps.add(2 + index % (n // 2 - 1))
        if index % 5 == 0:
            steps.add(n // 2)
        edges = {(min(u, (u + step) % n), max(u, (u + step) % n))
                 for u in range(n) for step in steps}
        yield "circulant", n, _edges_from_set(edges)

        # 4. Line graphs of random sparse parent graphs, truncated so the
        # number of line-graph vertices stays within the exact solver limit.
        parent_n = 7
        parent_edges = [(u, v) for u, v in combinations(range(parent_n), 2)
                        if rng.random() < (0.3, 0.48, 0.58)[index % 3]]
        parent_edges = parent_edges[:16]
        ln = len(parent_edges)
        edges = {(i, j) for i, j in combinations(range(ln), 2)
                 if set(parent_edges[i]) & set(parent_edges[j])}
        yield "line_graph", ln, _edges_from_set(edges)

        # 5. k-trees: chordal constructions formed by attaching each new
        # vertex to an existing clique of size k.
        t = (2, 3, 4)[index % 3]
        cliques = [tuple(range(t + 1))]
        edges = {(u, v) for u, v in combinations(range(t + 1), 2)}
        for vertex in range(t + 1, n):
            parent = rng.choice(cliques)
            attachment = tuple(sorted(rng.sample(parent, t)))
            for u in attachment:
                edges.add((min(u, vertex), max(u, vertex)))
            cliques.append(attachment + (vertex,))
        yield "k_tree", n, _edges_from_set(edges)


def greedy_clique_lower_bound(n: int, edges: tuple[tuple[int, int], ...],
                              *, backend="python") -> int:
    """Return the size of an actual clique, hence a certified chi lower bound."""
    if backend == "rust":
        from witnora_ve import greedy_clique_lower_bound_native
        return greedy_clique_lower_bound_native(n, list(edges))
    if backend != "python":
        raise ValueError("unknown greedy clique backend")
    if n == 0:
        return 0
    adjacency = [set() for _ in range(n)]
    for u, v in edges:
        adjacency[u].add(v)
        adjacency[v].add(u)
    best = 1
    for start in range(n):
        candidates = adjacency[start].copy()
        clique_size = 1
        while candidates:
            chosen = max(candidates, key=lambda v: (
                len(adjacency[v] & candidates), len(adjacency[v]), -v))
            clique_size += 1
            candidates &= adjacency[chosen]
        best = max(best, clique_size)
    return best


def ungated_repair(n: int, edges: tuple[tuple[int, int], ...],
                   *, backend="python") -> dict:
    """No chromatic-oracle calls, with capped local search per ordinary graph."""
    base = _dsatur_greedy_coloring(n, edges)
    best = {"bound": base["bound"], "coloring": base["coloring"], "stage": "dsatur"}
    # A witnessed clique of size k certifies that a proper k-coloring is
    # optimal; no exact chromatic oracle or speculative repair is needed.
    if greedy_clique_lower_bound(n, edges, backend=backend) == base["bound"]:
        return {**best, "stage": "clique_certified"}
    multi = multistart_dsatur(n, edges, starts=8)
    if multi["bound"] < best["bound"]:
        best = {**multi, "stage": "multistart"}
    if best["bound"] == base["bound"]:
        local = bounded_recolor(n, edges, base["coloring"],
                                max_changed=5, max_nodes=3000, backend=backend)
        if local["bound"] < best["bound"]:
            best = {**local, "stage": "local_recolor"}
    if best["bound"] == base["bound"]:
        single = kempe_repair(n, edges, base["coloring"],
                              max_swaps=25, max_nodes_each=400, backend=backend)
        if single["bound"] < best["bound"]:
            best = {**single, "stage": "single_kempe"}
    if best["bound"] == base["bound"]:
        double = double_kempe_repair(n, edges, base["coloring"],
                                    first_limit=8, second_limit=8,
                                    total_limit=40, recolor_nodes=300,
                                    backend=backend)
        if double["bound"] < best["bound"]:
            best = {**double, "stage": "double_kempe"}
    assert _checked(n, edges, best["coloring"])
    return best


def run_structured_study(*, backend="python") -> dict:
    plan = {"seed": 20261102, "families": ["planted_coloring", "bipartite",
            "circulant", "line_graph", "k_tree"], "per_family": 60,
            "total": 300, "oracle_gated": False}
    stats = {"graphs": 0, "dsatur_failures": 0,
             "repair_improvements": 0, "repair_fixes_failures": 0,
             "repair_remaining_failures": 0, "clique_certified": 0,
             "dsatur_seconds": 0.0,
             "repair_seconds": 0.0, "by_family": {}}
    examples = {"first_improvement": None, "first_unresolved": None}
    for family, n, edges in structured_graphs():
        group = stats["by_family"].setdefault(
            family, {"graphs": 0, "dsatur_failures": 0,
                     "repair_improvements": 0, "repair_remaining_failures": 0})
        start = perf_counter()
        base = _dsatur_greedy_coloring(n, edges)
        stats["dsatur_seconds"] += perf_counter() - start
        start = perf_counter()
        repaired = ungated_repair(n, edges, backend=backend)
        stats["repair_seconds"] += perf_counter() - start

        # Scoring oracle called only AFTER the full repair decision.
        better_than_greedy = exact_k_coloring(n, edges, base["bound"] - 1,
                                             backend=backend)
        better_than_repair = exact_k_coloring(n, edges, repaired["bound"] - 1,
                                             backend=backend)
        dsatur_failed = better_than_greedy is not None
        repair_failed = better_than_repair is not None
        improved = repaired["bound"] < base["bound"]
        assert not improved or dsatur_failed
        assert repaired["bound"] <= base["bound"]
        stats["graphs"] += 1
        stats["dsatur_failures"] += dsatur_failed
        stats["repair_improvements"] += improved
        stats["clique_certified"] += repaired["stage"] == "clique_certified"
        stats["repair_fixes_failures"] += dsatur_failed and not repair_failed
        stats["repair_remaining_failures"] += repair_failed
        group["graphs"] += 1
        group["dsatur_failures"] += dsatur_failed
        group["repair_improvements"] += improved
        group["repair_remaining_failures"] += repair_failed
        details = {"family": family, "n": n, "edges": [list(e) for e in edges],
                   "dsatur": base, "repair": repaired,
                   "better_than_greedy_witness": better_than_greedy,
                   "better_than_repair_witness": better_than_repair}
        if improved and examples["first_improvement"] is None:
            examples["first_improvement"] = details
        if repair_failed and examples["first_unresolved"] is None:
            examples["first_unresolved"] = details
    return {"plan": plan, "statistics": stats, "examples": examples,
            "novelty_verified": False, "lean_verified": False,
            "promoted": False}
