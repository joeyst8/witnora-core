"""Adversarial search for deterministic DSATUR coloring failures.

A failure is certified by a concrete proper coloring with fewer colors than
the DSATUR witness. Exact chromatic numbers are computed by an independent
backtracking k-colorability decision procedure, never inferred from DSATUR.
"""
from __future__ import annotations

from itertools import combinations
import random

from .nonedge_matching_bound import _dsatur_greedy_coloring, matching_color_bound
from .graph_conjecture_lab import graph_metrics


def exact_k_coloring(n: int, edges: tuple[tuple[int, int], ...],
                     k: int) -> list[int] | None:
    """Exhaustive k-colorability with color-symmetry pruning; n <= 16."""
    if not 0 <= n <= 16 or k < 0:
        raise ValueError("supported n <= 16 and nonnegative k")
    if len(set(edges)) != len(edges) or any(not 0 <= u < v < n for u, v in edges):
        raise ValueError("invalid simple graph")
    if n == 0:
        return [] if k >= 0 else None
    if k == 0:
        return None
    neighbors = [set() for _ in range(n)]
    for u, v in edges:
        neighbors[u].add(v)
        neighbors[v].add(u)
    colors = [-1] * n

    def search(used: int, remaining: int) -> bool:
        if remaining == 0:
            return True

        def priority(v: int):
            available_neighbor_colors = {colors[u] for u in neighbors[v] if colors[u] >= 0}
            return (len(available_neighbor_colors), len(neighbors[v]), -v)

        chosen = max((v for v in range(n) if colors[v] < 0), key=priority)
        forbidden = {colors[u] for u in neighbors[chosen] if colors[u] >= 0}
        # Existing colors and at most one canonical new color; this explores
        # every coloring up to permutation of the color names.
        for color in range(min(used + 1, k)):
            if color in forbidden:
                continue
            colors[chosen] = color
            if search(max(used, color + 1), remaining - 1):
                return True
            colors[chosen] = -1
        return False

    if not search(0, n):
        return None
    assert all(colors[u] != colors[v] for u, v in edges)
    return colors.copy()


def chromatic_certificate(n: int, edges: tuple[tuple[int, int], ...],
                          upper: int) -> dict:
    """Return first feasible k and its witness, with all smaller k ruled out."""
    for k in range(0, upper + 1):
        witness = exact_k_coloring(n, edges, k)
        if witness is not None:
            return {"chi": k, "coloring": witness, "lower_k_unsat_checked": True}
    raise AssertionError("provided upper bound is not feasible")


def run_adversarial_search() -> dict:
    # Fixed sample plan before inspecting results.
    densities = (0.15, 0.30, 0.45, 0.60, 0.75)
    per_cell = 120
    n_values = (10, 12, 14, 16)
    rng = random.Random(20261031)
    stats = {"graphs": 0, "failures": 0, "by_n": {}, "by_density": {},
             "small_exact_crosschecks": 0, "matching_evaluated_failures": 0,
             "matching_beats_dsatur_on_failures": 0,
             "matching_fixes_dsatur_failures": 0}
    examples = []

    # Independently cross-check the decision procedure against the existing
    # subset-DP chromatic solver before searching larger graphs.
    for n in range(1, 8):
        for index in range(24):
            p = (index % 5 + 1) / 6
            edges = tuple((u, v) for u, v in combinations(range(n), 2)
                          if rng.random() < p)
            chi = graph_metrics(n, edges)["chi"]
            actual = chromatic_certificate(n, edges, n)["chi"]
            assert actual == chi, (n, edges, actual, chi)
            stats["small_exact_crosschecks"] += 1

    for n in n_values:
        for density in densities:
            for index in range(per_cell):
                edges = tuple((u, v) for u, v in combinations(range(n), 2)
                              if rng.random() < density)
                greedy = _dsatur_greedy_coloring(n, edges)
                stats["graphs"] += 1
                stats["by_n"][str(n)] = stats["by_n"].get(str(n), 0) + 1
                key = str(density)
                stats["by_density"][key] = stats["by_density"].get(key, 0) + 1

                improved = exact_k_coloring(n, edges, greedy["bound"] - 1)
                if improved is None:
                    continue
                exact = chromatic_certificate(n, edges, greedy["bound"] - 1)
                assert exact["chi"] < greedy["bound"]
                stats["failures"] += 1
                matching = None
                if n <= 11:
                    matching = matching_color_bound(n, edges)
                    stats["matching_evaluated_failures"] += 1
                    stats["matching_beats_dsatur_on_failures"] += matching["bound"] < greedy["bound"]
                    stats["matching_fixes_dsatur_failures"] += matching["bound"] == exact["chi"]
                if len(examples) < 10:
                    examples.append({
                        "n": n, "density": density, "sample_index": index,
                        "edges": [list(edge) for edge in edges],
                        "dsatur_bound": greedy["bound"],
                        "dsatur_coloring": greedy["coloring"],
                        "exact_chi": exact["chi"],
                        "better_coloring": exact["coloring"],
                        "matching_bound": matching["bound"] if matching else None,
                    })
    return {
        "plan": {"vertices": list(n_values), "densities": list(densities),
                 "samples_per_cell": per_cell, "seed": 20261031},
        "statistics": stats, "counterexamples": examples,
        "novelty_verified": False, "lean_verified": False, "promoted": False,
    }
