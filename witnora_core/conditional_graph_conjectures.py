"""Finite conditional and transformation conjectures, not formal theorems."""
from __future__ import annotations

from itertools import combinations

from .graph_conjecture_lab import graph_metrics, graphs

CONDITIONS = ("connected", "bipartite", "triangle_free", "tree")
RELATIONS = ("chi<=2", "omega<=2", "tau==nu", "m>=n-1", "alpha>=2")
TRANSFORM_METRICS = ("alpha", "tau", "omega", "chi", "nu", "delta")
TRANSFORMS = ("complement", "delete_vertex_0")


def graph_record(n, edges):
    edge_set = set(edges)
    neighbors = [set() for _ in range(n)]
    for u, v in edges:
        neighbors[u].add(v)
        neighbors[v].add(u)
    colors = {}
    parts = 0
    bipartite = True
    for start in range(n):
        if start in colors:
            continue
        parts += 1
        colors[start] = 0
        queue = [start]
        while queue:
            v = queue.pop()
            for neighbor in neighbors[v]:
                if neighbor not in colors:
                    colors[neighbor] = 1 - colors[v]
                    queue.append(neighbor)
                elif colors[neighbor] == colors[v]:
                    bipartite = False
    original = graph_metrics(n, edges)
    complement = tuple(pair for pair in combinations(range(n), 2)
                       if pair not in edge_set)
    deleted = tuple((u - 1, v - 1) for u, v in edges if u != 0 and v != 0)
    return {
        "n": n, "edges": edges, "original": original,
        "complement": graph_metrics(n, complement),
        "delete_vertex_0": graph_metrics(n - 1, deleted),
        "conditions": {
            "connected": parts == 1,
            "bipartite": bipartite,
            "triangle_free": original["omega"] <= 2,
            "tree": parts == 1 and len(edges) == n - 1,
        },
    }


def relation_holds(relation, m):
    return {
        "chi<=2": m["chi"] <= 2,
        "omega<=2": m["omega"] <= 2,
        "tau==nu": m["tau"] == m["nu"],
        "m>=n-1": m["m"] >= m["n"] - 1,
        "alpha>=2": m["alpha"] >= 2,
    }[relation]


def templates():
    for condition in CONDITIONS:
        for relation in RELATIONS:
            yield ("conditional", condition, relation, "")
    for transform in TRANSFORMS:
        for metric in TRANSFORM_METRICS:
            for direction in ("le", "ge", "eq"):
                yield ("transform", transform, metric, direction)
    yield ("cross", "alpha", "omega", "complement")
    yield ("cross", "omega", "alpha", "complement")


def statement(item):
    kind, a, b, c = item
    if kind == "conditional":
        return f"if {a}(G) then {b}"
    if kind == "transform":
        sign = {"le": "<=", "ge": ">=", "eq": "="}[c]
        return f"{b}({a}(G)) {sign} {b}(G)"
    return f"{a}(G) = {b}(complement(G))"


def holds(item, record):
    kind, a, b, c = item
    if kind == "conditional":
        return not record["conditions"][a] or relation_holds(b, record["original"])
    if kind == "cross":
        return record["original"][a] == record["complement"][b]
    left, right = record[a][b], record["original"][b]
    return {"le": left <= right, "ge": left >= right, "eq": left == right}[c]


def nonvacuous(item, training):
    kind, a, b, c = item
    if kind == "conditional":
        applicable = [r for r in training if r["conditions"][a]]
        outside = [r for r in training if not r["conditions"][a]]
        return (len(applicable) >= 20 and len(outside) >= 20
                and any(not relation_holds(b, r["original"]) for r in outside))
    if kind == "transform":
        return sum(r[a][b] != r["original"][b] for r in training) >= 20
    return True


def run_experiment(*, holdout_each: int = 120):
    if not 1 <= holdout_each <= 500:
        raise ValueError("invalid bounded holdout")
    training = [graph_record(n, edges) for n in range(1, 6)
                for _, edges in graphs(n)]
    holdout = [graph_record(n, edges) for n in (6, 7)
               for seed in (1491, 1601)
               for _, edges in graphs(n, limit=holdout_each, seed=seed)]
    candidates = [item for item in templates()
                  if nonvacuous(item, training)
                  and all(holds(item, r) for r in training)]
    survivors, falsified = [], []
    for item in candidates:
        counterexample = next((r for r in holdout if not holds(item, r)), None)
        if counterexample is None:
            survivors.append(statement(item))
        else:
            falsified.append({
                "conjecture": statement(item),
                "n": counterexample["n"],
                "edges": [list(e) for e in counterexample["edges"]],
            })
    return {
        "training_graphs": len(training), "holdout_graphs": len(holdout),
        "templates_considered": len(list(templates())),
        "nonvacuous_training_survivors": len(candidates),
        "holdout_survivors": sorted(survivors),
        "falsified_on_holdout": falsified,
        "lean_verified": False, "novelty_verified": False,
        "theorem_proven": False, "promoted": False,
    }
