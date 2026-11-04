"""Bounded repair prototypes for DSATUR coloring failures.

Two deliberately limited heuristics:
- seeded multistart vertex relabelings of deterministic DSATUR;
- a depth/effort-capped recoloring search allowing <=5 changed vertex colors.
Neither is a novelty claim or an exact chromatic algorithm.
"""
from __future__ import annotations

from itertools import combinations
import random

from .dsatur_adversarial_lab import exact_k_coloring
from .nonedge_matching_bound import _dsatur_greedy_coloring


def _checked(n: int, edges: tuple[tuple[int, int], ...], colors: list[int]) -> bool:
    return len(colors) == n and all(c >= 0 for c in colors) and all(
        colors[u] != colors[v] for u, v in edges)


def multistart_dsatur(n: int, edges: tuple[tuple[int, int], ...],
                      starts: int = 8) -> dict:
    if not 1 <= starts <= 32:
        raise ValueError("starts must be 1..32")
    baseline = _dsatur_greedy_coloring(n, edges)
    best = {"bound": baseline["bound"], "coloring": baseline["coloring"],
            "restart": 0}
    # Seed is determined by graph structure, not by process-salted hash().
    seed = (n * 2_654_435_761 + sum((u + 1) * 131 + (v + 1) * 977
           for u, v in edges)) % (1 << 32)
    rng = random.Random(seed)
    for trial in range(1, starts):
        perm = list(range(n))
        rng.shuffle(perm)
        relabeled = tuple(sorted((min(perm[u], perm[v]), max(perm[u], perm[v]))
                                 for u, v in edges))
        found = _dsatur_greedy_coloring(n, relabeled)
        colors = [found["coloring"][perm[v]] for v in range(n)]
        assert _checked(n, edges, colors)
        if found["bound"] < best["bound"]:
            best = {"bound": found["bound"], "coloring": colors,
                    "restart": trial}
    return best


def bounded_recolor(n: int, edges: tuple[tuple[int, int], ...],
                    initial: list[int], max_changed: int = 5,
                    max_nodes: int = 8000, *, backend="python") -> dict:
    """Try to remove one color using a budgeted local Hamming-distance search.

    Incomplete by design. Report exhaustion rather than claiming UNSAT.
    """
    if not _checked(n, edges, initial):
        raise ValueError("not a proper initial coloring")
    if max_changed < 0 or max_nodes < 1:
        raise ValueError("invalid budgets")
    if backend == "rust":
        from witnora_ve import color_bounded_recolor_native
        bound, coloring, improved, nodes, exhausted = color_bounded_recolor_native(
            n, list(edges), initial, max_changed, max_nodes)
        return {"bound": bound, "coloring": coloring, "improved": improved,
                "nodes": nodes, "exhausted": exhausted}
    if backend != "python":
        raise ValueError("unknown recoloring backend")
    k = max(initial, default=-1) + 1
    if k <= 1:
        return {"bound": k, "coloring": initial.copy(), "improved": False,
                "nodes": 0, "exhausted": False}
    adjacency = [set() for _ in range(n)]
    for u, v in edges:
        adjacency[u].add(v)
        adjacency[v].add(u)
    order = sorted(range(n), key=lambda v: (initial[v] != k - 1,
                                           -len(adjacency[v]), v))
    result = [-1] * n
    nodes = 0
    exhausted = False

    def visit(index: int, changed: int) -> bool:
        nonlocal nodes, exhausted
        nodes += 1
        if nodes > max_nodes:
            exhausted = True
            return False
        if index == n:
            return True
        v = order[index]
        original = initial[v]
        choices = list(range(k - 1))
        choices.sort(key=lambda c: (c != original, c))
        for color in choices:
            extra = color != original
            if changed + extra > max_changed:
                continue
            if any(result[u] == color for u in adjacency[v]):
                continue
            result[v] = color
            if visit(index + 1, changed + extra):
                return True
            result[v] = -1
            if exhausted:
                return False
        return False

    found = visit(0, 0)
    if found:
        assert _checked(n, edges, result)
        return {"bound": k - 1, "coloring": result.copy(), "improved": True,
                "nodes": nodes, "exhausted": exhausted}
    return {"bound": k, "coloring": initial.copy(), "improved": False,
            "nodes": nodes, "exhausted": exhausted}


def run_repair_experiment(*, backend="python") -> dict:
    densities = (0.15, 0.30, 0.45, 0.60, 0.75)
    orders = (10, 12, 14, 16)
    samples_per_cell = 120
    report = {"design": {"orders": list(orders), "densities": list(densities),
                        "per_cell": samples_per_cell,
                        "training_seed": 20261031, "holdout_seed": 20261101,
                        "starts": 8, "max_changed": 5, "max_nodes": 8000},
              "training": {}, "holdout": {}, "examples": {}}
    for partition, seed in (("training", 20261031), ("holdout", 20261101)):
        rng = random.Random(seed)
        # Mirror v21 generator's 168 crosschecks consumption on training.
        if partition == "training":
            for n in range(1, 8):
                for index in range(24):
                    p = (index % 5 + 1) / 6
                    _ = tuple((u, v) for u, v in combinations(range(n), 2)
                              if rng.random() < p)

        stats = {"graphs": 0, "dsatur_failures": 0,
                 "multistart_improvements": 0, "recolor_improvements": 0,
                 "combined_improvements": 0, "multistart_fixes": 0,
                 "recolor_fixes": 0, "combined_fixes": 0,
                 "budget_exhaustions": 0}
        example = None
        unresolved = None
        for n in orders:
            for density in densities:
                for index in range(samples_per_cell):
                    edges = tuple((u, v) for u, v in combinations(range(n), 2)
                                  if rng.random() < density)
                    original = _dsatur_greedy_coloring(n, edges)
                    # An independently checked absence of any smaller coloring
                    # establishes that repair cannot improve this instance.
                    # Expensive local search is reserved for verified failures.
                    exact_better = exact_k_coloring(n, edges, original["bound"] - 1,
                                                    backend=backend)
                    failed = exact_better is not None
                    if failed:
                        multistart = multistart_dsatur(n, edges, 8)
                        recolor = bounded_recolor(n, edges, original["coloring"],
                                                   backend=backend)
                    else:
                        multistart = {"bound": original["bound"], "coloring": original["coloring"],
                                      "restart": 0}
                        recolor = {"bound": original["bound"], "coloring": original["coloring"],
                                   "improved": False, "nodes": 0, "exhausted": False}
                    combined = min(multistart["bound"], recolor["bound"])
                    stats["graphs"] += 1
                    stats["dsatur_failures"] += failed
                    stats["multistart_improvements"] += multistart["bound"] < original["bound"]
                    stats["recolor_improvements"] += recolor["bound"] < original["bound"]
                    stats["combined_improvements"] += combined < original["bound"]
                    stats["multistart_fixes"] += failed and multistart["bound"] == original["bound"] - 1
                    stats["recolor_fixes"] += failed and recolor["bound"] == original["bound"] - 1
                    stats["combined_fixes"] += failed and combined == original["bound"] - 1
                    stats["budget_exhaustions"] += recolor["exhausted"]
                    if failed and combined == original["bound"] and unresolved is None:
                        unresolved = {"n": n, "density": density, "index": index,
                                      "edges": [list(e) for e in edges],
                                      "dsatur": original, "multistart": multistart,
                                      "bounded_recolor": recolor,
                                      "better_witness": exact_better}
                    if failed and example is None:
                        example = {
                            "n": n, "density": density, "index": index,
                            "edges": [list(e) for e in edges],
                            "dsatur": original,
                            "multistart": multistart, "bounded_recolor": recolor,
                            "better_witness": exact_better,
                        }
        report[partition] = stats
        report["examples"][partition] = example
        report["examples"][partition + "_unresolved"] = unresolved
    report.update({"novelty_verified": False, "lean_verified": False,
                   "promoted": False})
    return report
