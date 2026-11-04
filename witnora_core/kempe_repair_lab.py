"""Kempe-component swaps followed by bounded recoloring.

Research-only repair experiment. A Kempe swap exchanges two colors on one
connected component of their induced two-color subgraph; this preserves
proper coloring. We then try the already-defined bounded five-change repair.
"""
from __future__ import annotations

from itertools import combinations
import random

from .color_repair_lab import bounded_recolor, multistart_dsatur, _checked
from .dsatur_adversarial_lab import exact_k_coloring
from .nonedge_matching_bound import _dsatur_greedy_coloring


def kempe_swaps(n: int, edges: tuple[tuple[int, int], ...],
                initial: list[int], *, backend="python") -> list[dict]:
    if not _checked(n, edges, initial):
        raise ValueError("invalid initial coloring")
    if backend == "rust":
        from witnora_ve import kempe_swaps_native
        return [{"coloring": colors, "swapped_colors": pair, "component": component}
                for colors, pair, component in kempe_swaps_native(n, list(edges), initial)]
    if backend != "python":
        raise ValueError("unknown Kempe swap backend")
    neighbors = [set() for _ in range(n)]
    for u, v in edges:
        neighbors[u].add(v)
        neighbors[v].add(u)
    k = max(initial, default=-1) + 1
    variants = []
    seen_colorings = {tuple(initial)}
    for a, b in combinations(range(k), 2):
        eligible = {v for v in range(n) if initial[v] in (a, b)}
        seen = set()
        for start in sorted(eligible):
            if start in seen:
                continue
            component = {start}
            todo = [start]
            seen.add(start)
            while todo:
                for v in sorted(neighbors[todo.pop()] & eligible):
                    if v not in seen:
                        seen.add(v)
                        component.add(v)
                        todo.append(v)
            result = initial.copy()
            for v in component:
                result[v] = b if initial[v] == a else a
            key = tuple(result)
            if key in seen_colorings:
                continue
            seen_colorings.add(key)
            assert _checked(n, edges, result)
            variants.append({"coloring": result, "swapped_colors": [a, b],
                             "component": sorted(component)})
    return variants


def kempe_repair(n: int, edges: tuple[tuple[int, int], ...],
                 initial: list[int], max_swaps: int = 90,
                 max_nodes_each: int = 2500, *, backend="python") -> dict:
    if max_swaps < 1 or max_nodes_each < 1:
        raise ValueError("invalid budgets")
    original_k = max(initial, default=-1) + 1
    attempts = 0
    for variant in kempe_swaps(n, edges, initial, backend=backend):
        if attempts >= max_swaps:
            break
        attempts += 1
        used = sorted(set(variant["coloring"]))
        if len(used) < original_k:
            compact = {c: i for i, c in enumerate(used)}
            improved_colors = [compact[c] for c in variant["coloring"]]
            assert _checked(n, edges, improved_colors)
            return {"bound": len(used), "coloring": improved_colors,
                    "improved": True, "attempts": attempts,
                    "swapped_colors": variant["swapped_colors"],
                    "component": variant["component"], "recolor_nodes": 0}
        trial = bounded_recolor(n, edges, variant["coloring"],
                                max_changed=5, max_nodes=max_nodes_each,
                                backend=backend)
        if trial["improved"]:
            assert trial["bound"] == original_k - 1
            return {"bound": trial["bound"], "coloring": trial["coloring"],
                    "improved": True, "attempts": attempts,
                    "swapped_colors": variant["swapped_colors"],
                    "component": variant["component"],
                    "recolor_nodes": trial["nodes"]}
    return {"bound": original_k, "coloring": initial.copy(),
            "improved": False, "attempts": attempts,
            "swapped_colors": None, "component": [],
            "recolor_nodes": None}


def run_kempe_experiment(*, backend="python") -> dict:
    orders = (10, 12, 14, 16)
    densities = (0.15, 0.30, 0.45, 0.60, 0.75)
    per_cell = 120
    result = {"plan": {"orders": list(orders), "densities": list(densities),
                      "per_cell": per_cell,
                      "seeds": {"training": 20261031, "holdout": 20261101},
                      "max_swaps": 90, "max_nodes_each": 2500},
              "training": {}, "holdout": {}, "examples": {}}
    for partition, seed in (("training", 20261031), ("holdout", 20261101)):
        rng = random.Random(seed)
        if partition == "training":
            # Identical random-generator offset to v21/v22.
            for n in range(1, 8):
                for index in range(24):
                    p = (index % 5 + 1) / 6
                    _ = tuple((u, v) for u, v in combinations(range(n), 2)
                              if rng.random() < p)
        stats = {"graphs": 0, "dsatur_failures": 0,
                 "v22_fixed": 0, "v22_unresolved": 0,
                 "kempe_fixes_additional": 0, "final_unresolved": 0,
                 "total_kempe_swap_attempts": 0}
        examples = {"first_kempe_fix": None, "first_unresolved": None}
        for n in orders:
            for density in densities:
                for index in range(per_cell):
                    edges = tuple((u, v) for u, v in combinations(range(n), 2)
                                  if rng.random() < density)
                    base = _dsatur_greedy_coloring(n, edges)
                    smaller = exact_k_coloring(n, edges, base["bound"] - 1,
                                               backend=backend)
                    stats["graphs"] += 1
                    if smaller is None:
                        continue
                    stats["dsatur_failures"] += 1
                    restarts = multistart_dsatur(n, edges, starts=8)
                    local = bounded_recolor(n, edges, base["coloring"],
                                            max_changed=5, max_nodes=8000,
                                            backend=backend)
                    if min(restarts["bound"], local["bound"]) < base["bound"]:
                        stats["v22_fixed"] += 1
                        continue
                    stats["v22_unresolved"] += 1
                    attempt = kempe_repair(n, edges, base["coloring"], backend=backend)
                    stats["total_kempe_swap_attempts"] += attempt["attempts"]
                    details = {"n": n, "density": density, "index": index,
                               "edges": [list(e) for e in edges],
                               "dsatur": base, "better_witness": smaller,
                               "kempe": attempt}
                    if attempt["improved"]:
                        stats["kempe_fixes_additional"] += 1
                        if examples["first_kempe_fix"] is None:
                            examples["first_kempe_fix"] = details
                    else:
                        stats["final_unresolved"] += 1
                        if examples["first_unresolved"] is None:
                            examples["first_unresolved"] = details
        result[partition] = stats
        result["examples"][partition] = examples
    result.update({"lean_verified": False, "novelty_verified": False,
                   "promoted": False})
    return result
