"""Experimental coloring upper bound via matching nonedges in vertex covers.

For a cover S, pair disjoint nonadjacent cover vertices, assign each pair
one color, give unpaired cover vertices distinct colors, and give the
independent complement one additional color (if nonempty). This is a
constructive finite-data upper bound, not a novelty claim.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations
import random

from .graph_conjecture_lab import graph_metrics, graphs
from .targeted_graph_theorems import special_graphs


def _popcount(mask: int) -> int:
    return mask.bit_count()


def matching_color_bound(n: int, edges: tuple[tuple[int, int], ...]) -> dict:
    if not 0 <= n <= 11:
        raise ValueError("bounded study only")
    edge_set = set(edges)
    if len(edge_set) != len(edges) or any(not 0 <= u < v < n for u, v in edges):
        raise ValueError("invalid simple graph")
    neighbors = [0] * n
    for u, v in edge_set:
        neighbors[u] |= 1 << v
        neighbors[v] |= 1 << u
    full = (1 << n) - 1

    independent = [False] * (1 << n)
    independent[0] = True
    for mask in range(1, 1 << n):
        bit = mask & -mask
        v = bit.bit_length() - 1
        rest = mask ^ bit
        independent[mask] = independent[rest] and not (neighbors[v] & rest)

    @lru_cache(None)
    def nonedge_matching(mask: int) -> tuple[tuple[int, int], ...]:
        if mask == 0:
            return ()
        bit = mask & -mask
        u = bit.bit_length() - 1
        rest = mask ^ bit
        best = nonedge_matching(rest)
        options = rest & ~neighbors[u]
        while options:
            partner_bit = options & -options
            options ^= partner_bit
            v = partner_bit.bit_length() - 1
            candidate = ((u, v),) + nonedge_matching(rest ^ partner_bit)
            if len(candidate) > len(best) or (len(candidate) == len(best) and candidate < best):
                best = candidate
        return best

    best = None
    for cover in range(1 << n):
        outside = full ^ cover
        if not independent[outside]:
            continue
        matching = nonedge_matching(cover)
        bound = _popcount(cover) - len(matching) + (1 if outside else 0)
        trial = (bound, _popcount(cover), cover, matching)
        if best is None or trial < best:
            best = trial

    assert best is not None
    bound, _, cover, matching = best
    colors = [-1] * n
    next_color = 0
    for u, v in matching:
        assert not (neighbors[u] & (1 << v))
        colors[u] = colors[v] = next_color
        next_color += 1
    for u in range(n):
        if (cover & (1 << u)) and colors[u] == -1:
            colors[u] = next_color
            next_color += 1
    if full ^ cover:
        for u in range(n):
            if not (cover & (1 << u)):
                colors[u] = next_color
        next_color += 1

    assert next_color == bound
    assert all(color >= 0 for color in colors)
    assert all(colors[u] != colors[v] for u, v in edges)
    return {
        "bound": bound,
        "cover": [u for u in range(n) if cover & (1 << u)],
        "paired_nonedges": [list(pair) for pair in matching],
        "coloring": colors,
    }



def _componentwise_baseline(n: int, edges: tuple[tuple[int, int], ...]) -> int:
    neighbors = [set() for _ in range(n)]
    for u, v in edges:
        neighbors[u].add(v)
        neighbors[v].add(u)
    seen = set()
    bound = 0
    for start in range(n):
        if start in seen:
            continue
        component = []
        queue = [start]
        seen.add(start)
        for u in queue:
            component.append(u)
            for v in sorted(neighbors[u]):
                if v not in seen:
                    seen.add(v)
                    queue.append(v)
        local = {v: i for i, v in enumerate(sorted(component))}
        local_edges = tuple((local[u], local[v]) for u, v in edges
                            if u in local and v in local)
        values = graph_metrics(len(component), local_edges)
        bound = max(bound, values["tau"], values["omega"])
    return bound

def _edge_list(n: int, mask: int) -> tuple[tuple[int, int], ...]:
    pairs = list(combinations(range(n), 2))
    return tuple(pair for i, pair in enumerate(pairs) if mask & (1 << i))


def _sample_holdout():
    for n in range(7, 12):
        rng = random.Random(9241 + n)
        for density in (0.10, 0.30, 0.50, 0.70, 0.90):
            count = {7: 24, 8: 24, 9: 16, 10: 10, 11: 6}[n]
            for index in range(count):
                edges = tuple((u, v) for u, v in combinations(range(n), 2)
                              if rng.random() < density)
                yield f"random_n{n}_p{density}_i{index}", n, edges
    yield from special_graphs()


def run_experiment() -> dict:
    tally = {
        "graphs": 0, "matching_strict_improvements": 0,
        "matching_worse_than_baseline": 0,
        "matching_exact": 0, "baseline_exact": 0, "hybrid_exact": 0,
        "strong_baseline_exact": 0, "strong_hybrid_exact": 0,
        "matching_strict_improvements_over_strong": 0,
        "hybrid_counterexamples": 0,
    }
    examples = {"first_improvement": None, "first_matching_gap": None,
                "first_hybrid_gap": None}

    def inspect(label: str, n: int, edges: tuple[tuple[int, int], ...]):
        values = graph_metrics(n, edges)
        attempt = matching_color_bound(n, edges)
        baseline = max(values["tau"], values["omega"])
        component_bound = _componentwise_baseline(n, edges)
        greedy_bound = values["delta"] + 1 if n else 0
        strong_baseline = min(baseline, component_bound, greedy_bound)
        hybrid = min(attempt["bound"], baseline)
        strong_hybrid = min(attempt["bound"], strong_baseline)
        if not values["chi"] <= attempt["bound"]:
            raise AssertionError("invalid upper bound")
        if not values["chi"] <= hybrid or not values["chi"] <= strong_hybrid:
            raise AssertionError("hybrid is not an upper bound")
        tally["graphs"] += 1
        tally["matching_strict_improvements"] += attempt["bound"] < baseline
        tally["matching_worse_than_baseline"] += attempt["bound"] > baseline
        tally["matching_exact"] += attempt["bound"] == values["chi"]
        tally["baseline_exact"] += baseline == values["chi"]
        tally["hybrid_exact"] += hybrid == values["chi"]
        tally["strong_baseline_exact"] += strong_baseline == values["chi"]
        tally["strong_hybrid_exact"] += strong_hybrid == values["chi"]
        tally["matching_strict_improvements_over_strong"] += attempt["bound"] < strong_baseline
        if hybrid < values["chi"]:
            tally["hybrid_counterexamples"] += 1
        details = {
            "family": label, "n": n, "edges": [list(e) for e in edges],
            "chi": values["chi"], "tau": values["tau"], "omega": values["omega"],
            "baseline": baseline, "matching_bound": attempt["bound"],
            "hybrid": hybrid, "strong_baseline": strong_baseline,
            "strong_hybrid": strong_hybrid, "witness": attempt,
        }
        if attempt["bound"] < baseline and examples["first_improvement"] is None:
            examples["first_improvement"] = details
        if attempt["bound"] > values["chi"] and examples["first_matching_gap"] is None:
            examples["first_matching_gap"] = details
        if hybrid > values["chi"] and examples["first_hybrid_gap"] is None:
            examples["first_hybrid_gap"] = details

    for n in range(1, 7):
        for _, edges in graphs(n):
            inspect("exhaustive", n, edges)
    training = dict(tally)
    for label, n, edges in _sample_holdout():
        inspect(label, n, edges)
    holdout = {key: tally[key] - training[key] for key in tally}
    return {
        "hypothesis": "chi <= min(max(tau, omega), min_cover_S(|S| - nu(nonedges(G[S])) + [V\\S != empty]))",
        "training": training,
        "holdout": holdout,
        "examples": examples,
        "lean_verified": False,
        "novelty_verified": False,
        "theorem_proven": False,
        "promoted": False,
    }
