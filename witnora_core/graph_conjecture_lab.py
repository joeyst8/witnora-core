"""Finite graph-invariant conjecture mining with explicit counterexample search.

Every output is a finite-data hypothesis, never a theorem or novelty claim.
"""
from __future__ import annotations

from itertools import combinations
from functools import lru_cache
import random

METRICS = ("n", "m", "alpha", "tau", "omega", "chi", "nu", "delta")


def graph_metrics(n: int, edges: tuple[tuple[int, int], ...]) -> dict[str, int]:
    if not 0 <= n <= 11 or any(not 0 <= u < v < n for u, v in edges):
        raise ValueError("invalid bounded simple graph")
    neighbors = [0] * n
    for u, v in edges:
        neighbors[u] |= 1 << v
        neighbors[v] |= 1 << u
    independent = [False] * (1 << n)
    independent[0] = True
    for mask in range(1, 1 << n):
        bit = mask & -mask
        v = bit.bit_length() - 1
        rest = mask ^ bit
        independent[mask] = independent[rest] and not (neighbors[v] & rest)
    alpha = max(mask.bit_count() for mask in range(1 << n) if independent[mask])
    clique = max(mask.bit_count() for mask in range(1 << n)
                 if all((neighbors[v] & (mask ^ (1 << v))) == (mask ^ (1 << v))
                        for v in range(n) if mask & (1 << v)))

    @lru_cache(None)
    def chromatic(mask):
        if not mask:
            return 0
        anchor = mask & -mask
        sub = mask
        best = n + 1
        while sub:
            if sub & anchor and independent[sub]:
                best = min(best, 1 + chromatic(mask ^ sub))
            sub = (sub - 1) & mask
        return best

    @lru_cache(None)
    def matching(mask):
        if not mask:
            return 0
        bit = mask & -mask
        v = bit.bit_length() - 1
        rest = mask ^ bit
        answer = matching(rest)
        possible = neighbors[v] & rest
        while possible:
            other = possible & -possible
            possible ^= other
            answer = max(answer, 1 + matching(rest ^ other))
        return answer

    return {
        "n": n, "m": len(edges), "alpha": alpha, "tau": n - alpha,
        "omega": clique, "chi": chromatic((1 << n) - 1),
        "nu": matching((1 << n) - 1),
        "delta": max((x.bit_count() for x in neighbors), default=0),
    }


def graphs(n: int, *, limit: int | None = None, seed: int = 0):
    pairs = list(combinations(range(n), 2))
    total = 1 << len(pairs)
    if limit is None:
        masks = range(total)
    else:
        rng = random.Random(seed)
        masks = rng.sample(range(total), min(limit, total))
    for mask in masks:
        yield n, tuple(pair for i, pair in enumerate(pairs) if mask & (1 << i))


def candidate_templates():
    for a in METRICS:
        for b in METRICS:
            if a != b:
                yield ("le", a, b, "")
    for a, b in combinations(METRICS, 2):
        for c in METRICS:
            if c not in (a, b):
                yield ("sum_eq", a, b, c)


def holds(template, metrics):
    kind, a, b, c = template
    if kind == "le":
        return metrics[a] <= metrics[b]
    return metrics[a] + metrics[b] == metrics[c]


def name(template):
    kind, a, b, c = template
    return f"{a} <= {b}" if kind == "le" else f"{a} + {b} = {c}"


def discover_conjectures(*, training_max_n: int = 5,
                         holdout_seeds: tuple[int, ...] = (8123, 9341),
                         holdout_per_size: int = 150) -> dict:
    if training_max_n != 5 or holdout_per_size < 1 or holdout_per_size > 1000:
        raise ValueError("predeclared bounded conjecture study only")
    training = [graph_metrics(n, edges) for n in range(1, 6)
                for _, edges in graphs(n)]
    templates = [x for x in candidate_templates()
                 if all(holds(x, row) for row in training)]
    holdout = [(n, edges) for n in (6, 7)
               for seed in holdout_seeds
               for _, edges in graphs(n, limit=holdout_per_size, seed=seed)]
    surviving, rejected = [], []
    for template in templates:
        counterexample = next(((n, edges, graph_metrics(n, edges))
                               for n, edges in holdout
                               if not holds(template, graph_metrics(n, edges))), None)
        if counterexample is None:
            surviving.append(name(template))
        else:
            n, edges, metrics = counterexample
            rejected.append({"conjecture": name(template), "n": n,
                             "edges": [list(e) for e in edges], "metrics": metrics})
    return {
        "training_graphs": len(training), "holdout_graphs": len(holdout),
        "templates_considered": len(list(candidate_templates())),
        "training_survivors": len(templates),
        "holdout_survivors": sorted(surviving),
        "falsified_on_holdout": rejected,
        "theorem_proven": False, "novelty_verified": False,
        "lean_verified": False, "promoted": False,
    }
