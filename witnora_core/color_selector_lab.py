"""Learn a cheap, transparent repair selector on train only.

The selected rule is frozen before unseen holdout and structured-graph scoring.
Exact k-colorability supplies labels for evaluation, not runtime decisions.
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations
from time import perf_counter
import random

from .dsatur_adversarial_lab import exact_k_coloring
from .nonedge_matching_bound import _dsatur_greedy_coloring
from .structured_coloring_study import (greedy_clique_lower_bound,
                                         structured_graphs, ungated_repair)


RULES = (
    "uncertified",
    "gap_ge_2",
    "gap_ge_3",
    "uncertified_last_le_1",
    "uncertified_last_le_2",
    "uncertified_last_le_3",
    "uncertified_singleton",
    "uncertified_minclass_le_2",
    "uncertified_k_ge_4",
    "uncertified_last_le_2_or_singleton",
)


def signals(n: int, edges: tuple[tuple[int, int], ...],
            colors: list[int], *, backend="python") -> dict:
    if backend == "rust":
        from witnora_ve import color_selector_signals_native
        k, clique, gap, last_size, min_class, singleton = color_selector_signals_native(
            n, list(edges), colors)
        return {"k": k, "clique": clique, "gap": gap,
                "last_size": last_size, "min_class": min_class,
                "singleton": singleton}
    if backend != "python":
        raise ValueError("unknown selector signal backend")
    k = max(colors, default=-1) + 1
    witnessed_clique = greedy_clique_lower_bound(n, edges)
    sizes = Counter(colors)
    return {
        "k": k, "clique": witnessed_clique, "gap": k - witnessed_clique,
        "last_size": sizes[k - 1] if k else 0,
        "min_class": min(sizes.values(), default=0),
        "singleton": sum(value == 1 for value in sizes.values()),
    }


def triggers(rule: str, f: dict, *, backend="python") -> bool:
    if backend == "rust":
        from witnora_ve import color_selector_triggers_native
        return color_selector_triggers_native(
            rule, f["k"], f["gap"], f["last_size"], f["min_class"], f["singleton"])
    if backend != "python":
        raise ValueError("unknown selector trigger backend")
    g = f["gap"] > 0
    if rule == "uncertified":
        return g
    if rule == "gap_ge_2":
        return f["gap"] >= 2
    if rule == "gap_ge_3":
        return f["gap"] >= 3
    if rule == "uncertified_last_le_1":
        return g and f["last_size"] <= 1
    if rule == "uncertified_last_le_2":
        return g and f["last_size"] <= 2
    if rule == "uncertified_last_le_3":
        return g and f["last_size"] <= 3
    if rule == "uncertified_singleton":
        return g and f["singleton"] >= 1
    if rule == "uncertified_minclass_le_2":
        return g and f["min_class"] <= 2
    if rule == "uncertified_k_ge_4":
        return g and f["k"] >= 4
    if rule == "uncertified_last_le_2_or_singleton":
        return g and (f["last_size"] <= 2 or f["singleton"] >= 1)
    raise ValueError("unknown selector")


def _random_graphs(seed: int, training: bool):
    rng = random.Random(seed)
    if training:
        # v21 consumed these random numbers before the main sample grid.
        for n in range(1, 8):
            for i in range(24):
                p = (i % 5 + 1) / 6
                _ = tuple((u, v) for u, v in combinations(range(n), 2)
                          if rng.random() < p)
    for n in (10, 12, 14, 16):
        for p in (0.15, 0.30, 0.45, 0.60, 0.75):
            for _ in range(120):
                edges = tuple((u, v) for u, v in combinations(range(n), 2)
                              if rng.random() < p)
                yield "random", n, edges


def labeled_samples(graphs, *, backend="python"):
    for family, n, edges in graphs:
        greedy = _dsatur_greedy_coloring(n, edges)
        feature = signals(n, edges, greedy["coloring"], backend=backend)
        failure = exact_k_coloring(n, edges, greedy["bound"] - 1,
                                   backend=backend) is not None
        yield {"family": family, "n": n, "edges": edges,
               "dsatur": greedy, "signals": feature, "failure": failure}


def confusion(rows: list[dict], rule: str, *, backend="python") -> dict:
    positives = sum(row["failure"] for row in rows)
    candidates = [row for row in rows if triggers(rule, row["signals"],
                                                backend=backend)]
    true_positives = sum(row["failure"] for row in candidates)
    return {
        "graphs": len(rows), "failures": positives,
        "selected": len(candidates), "true_positives": true_positives,
        "missed": positives - true_positives,
        "false_positives": len(candidates) - true_positives,
        "recall": true_positives / positives if positives else 1.0,
        "precision": true_positives / len(candidates) if candidates else 0.0,
    }


def run_selector_study(*, backend="python") -> dict:
    training = list(labeled_samples(_random_graphs(20261031, True),
                                    backend=backend))
    train_scores = {rule: confusion(training, rule, backend=backend)
                    for rule in RULES}
    viable = [rule for rule in RULES if train_scores[rule]["recall"] >= 0.95]
    # Pick smallest workload among rules satisfying predeclared train recall
    # constraint; deterministic declaration order breaks ties.
    chosen = min(viable, key=lambda rule: (train_scores[rule]["selected"],
                                         RULES.index(rule)))
    holdout = list(labeled_samples(_random_graphs(20261101, False),
                                   backend=backend))
    structured = list(labeled_samples(structured_graphs(), backend=backend))
    evaluations = {}
    for label, rows in (("holdout_random", holdout),
                        ("holdout_structured", structured)):
        frozen = confusion(rows, chosen, backend=backend)
        full = confusion(rows, "uncertified", backend=backend)
        baseline_time = 0.0
        conditional_time = 0.0
        repair_improvements = 0
        remaining_failures = 0
        examples = {"first_missed_failure": None}
        for row in rows:
            n, edges = row["n"], row["edges"]
            # Timing here includes DSATUR in each respective end-to-end
            # pipeline; independent labeling happened before these calls.
            t = perf_counter()
            _dsatur_greedy_coloring(n, edges)
            baseline_time += perf_counter() - t
            t = perf_counter()
            fresh_greedy = _dsatur_greedy_coloring(n, edges)
            fresh_signals = signals(n, edges, fresh_greedy["coloring"],
                                    backend=backend)
            assert fresh_signals == row["signals"]
            if triggers(chosen, fresh_signals, backend=backend):
                candidate = ungated_repair(n, edges, backend=backend)
            else:
                candidate = fresh_greedy
            conditional_time += perf_counter() - t
            improved = candidate["bound"] < row["dsatur"]["bound"]
            repair_improvements += improved
            unresolved = exact_k_coloring(n, edges, candidate["bound"] - 1,
                                          backend=backend) is not None
            remaining_failures += unresolved
            if row["failure"] and not triggers(chosen, row["signals"], backend=backend) and examples["first_missed_failure"] is None:
                examples["first_missed_failure"] = {
                    "n": n, "family": row["family"],
                    "edges": [list(e) for e in edges],
                    "signals": row["signals"],
                    "dsatur_colors": row["dsatur"]["bound"],
                }
        evaluations[label] = {
            "selector": frozen, "uncertified_reference": full,
            "actual_improvements": repair_improvements,
            "remaining_failures": remaining_failures,
            "baseline_seconds": baseline_time,
            "conditional_seconds": conditional_time,
            "examples": examples,
        }
    return {"rules_predeclared": list(RULES), "chosen_rule": chosen,
            "train_scores": train_scores, "evaluations": evaluations,
            "novelty_verified": False, "lean_verified": False,
            "promoted": False}
