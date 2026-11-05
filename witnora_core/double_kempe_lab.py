"""Two-step Kempe swaps on the stubborn DSATUR repair failures.

Each move preserves proper coloring. The bounded local recoloring stage is
incomplete; a failure to find a coloring is never called an impossibility.
"""
from __future__ import annotations

from itertools import combinations
import random

from .color_repair_lab import bounded_recolor, multistart_dsatur, _checked
from .dsatur_adversarial_lab import exact_k_coloring
from .kempe_repair_lab import kempe_swaps, kempe_repair
from .nonedge_matching_bound import _dsatur_greedy_coloring


def double_kempe_repair(n: int, edges: tuple[tuple[int, int], ...],
                        original: list[int], first_limit: int = 30,
                        second_limit: int = 30, total_limit: int = 500,
                        recolor_nodes: int = 1200, *, backend="python") -> dict:
    if any(x < 1 for x in (first_limit, second_limit, total_limit, recolor_nodes)):
        raise ValueError("positive search budgets required")
    if not _checked(n, edges, original):
        raise ValueError("invalid initial proper coloring")
    if backend == "rust":
        from witnora_ve import double_kempe_repair_native
        (bound, coloring, improved, attempts, first_swap, second_swap,
         recolor_count) = double_kempe_repair_native(
            n, list(edges), original, first_limit, second_limit,
            total_limit, recolor_nodes)
        return {"bound": bound, "coloring": coloring, "improved": improved,
                "attempts": attempts, "first_swap": first_swap,
                "second_swap": second_swap, "recolor_nodes": recolor_count}
    if backend != "python":
        raise ValueError("unknown double Kempe backend")
    original_k = max(original, default=-1) + 1
    attempts = 0
    visited = {tuple(original)}

    for first in kempe_swaps(n, edges, original)[:first_limit]:
        # The previous stage already checks every single swap. Two distinct
        # component moves can reach a different region of the coloring space.
        for second in kempe_swaps(n, edges, first["coloring"])[:second_limit]:
            colors = second["coloring"]
            key = tuple(colors)
            if key in visited:
                continue
            visited.add(key)
            attempts += 1
            used = sorted(set(colors))
            if len(used) < original_k:
                label = {color: i for i, color in enumerate(used)}
                compressed = [label[color] for color in colors]
                assert _checked(n, edges, compressed)
                return {"bound": len(used), "coloring": compressed,
                        "improved": True, "attempts": attempts,
                        "first_swap": first["component"],
                        "second_swap": second["component"],
                        "recolor_nodes": 0}
            trial = bounded_recolor(n, edges, colors, max_changed=5,
                                    max_nodes=recolor_nodes)
            if trial["improved"]:
                assert _checked(n, edges, trial["coloring"])
                return {"bound": trial["bound"], "coloring": trial["coloring"],
                        "improved": True, "attempts": attempts,
                        "first_swap": first["component"],
                        "second_swap": second["component"],
                        "recolor_nodes": trial["nodes"]}
            if attempts >= total_limit:
                break
        if attempts >= total_limit:
            break
    return {"bound": original_k, "coloring": original.copy(),
            "improved": False, "attempts": attempts, "first_swap": [],
            "second_swap": [], "recolor_nodes": None}


def run_double_kempe_experiment(*, backend="python") -> dict:
    orders = (10, 12, 14, 16)
    densities = (0.15, 0.30, 0.45, 0.60, 0.75)
    per_cell = 120
    report = {"plan": {"orders": list(orders), "densities": list(densities),
                      "per_cell": per_cell, "first_limit": 30, "second_limit": 30,
                      "total_limit": 500, "recolor_nodes": 1200},
              "training": {}, "holdout": {}, "examples": {}}
    for partition, seed in (("training", 20261031), ("holdout", 20261101)):
        rng = random.Random(seed)
        if partition == "training":
            for n in range(1, 8):
                for index in range(24):
                    p = (index % 5 + 1) / 6
                    _ = tuple((u, v) for u, v in combinations(range(n), 2)
                              if rng.random() < p)
        stats = {"graphs": 0, "dsatur_failures": 0,
                 "v22_fixed": 0, "v23_additional_fixed": 0,
                 "v23_unresolved": 0, "double_kempe_additional_fixed": 0,
                 "final_unresolved": 0, "double_swap_attempts": 0}
        examples = {"first_fix": None, "first_unresolved": None}
        for n in orders:
            for density in densities:
                for index in range(per_cell):
                    edges = tuple((u, v) for u, v in combinations(range(n), 2)
                                  if rng.random() < density)
                    base = _dsatur_greedy_coloring(n, edges)
                    better = exact_k_coloring(n, edges, base["bound"] - 1,
                                              backend=backend)
                    stats["graphs"] += 1
                    if better is None:
                        continue
                    stats["dsatur_failures"] += 1
                    multi = multistart_dsatur(n, edges)
                    recolor = bounded_recolor(n, edges, base["coloring"],
                                             backend=backend)
                    if min(multi["bound"], recolor["bound"]) < base["bound"]:
                        stats["v22_fixed"] += 1
                        continue
                    single = kempe_repair(n, edges, base["coloring"],
                                          backend=backend)
                    if single["improved"]:
                        stats["v23_additional_fixed"] += 1
                        continue
                    stats["v23_unresolved"] += 1
                    attempt = double_kempe_repair(n, edges, base["coloring"],
                                                  backend=backend)
                    stats["double_swap_attempts"] += attempt["attempts"]
                    details = {"n": n, "density": density, "index": index,
                               "edges": [list(e) for e in edges],
                               "dsatur": base, "better_witness": better,
                               "double_kempe": attempt}
                    if attempt["improved"]:
                        stats["double_kempe_additional_fixed"] += 1
                        if examples["first_fix"] is None:
                            examples["first_fix"] = details
                    else:
                        stats["final_unresolved"] += 1
                        if examples["first_unresolved"] is None:
                            examples["first_unresolved"] = details
        report[partition] = stats
        report["examples"][partition] = examples
    report.update({"novelty_verified": False, "lean_verified": False,
                   "promoted": False})
    return report
