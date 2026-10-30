"""Bounded expression-grammar conjecture mining with holdout falsification.

Equality on finite graphs is evidence only. Novelty and theorem status remain
unreviewed/false for every candidate, including survivors.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from .graph_conjecture_lab import graph_metrics, graphs

ATOMS = ("n", "m", "alpha", "tau", "omega", "chi", "nu", "delta", "0", "1", "2")
OPS = ("+", "-", "*", "min", "max")


@dataclass(frozen=True)
class Expr:
    op: str
    a: str
    b: str = ""

    @property
    def label(self):
        if self.op == "atom":
            return self.a
        if self.op in ("min", "max"):
            return f"{self.op}({self.a},{self.b})"
        return f"({self.a}{self.op}{self.b})"

    @property
    def complexity(self):
        return 0 if self.op == "atom" else 1

    def evaluate(self, values):
        def value(x):
            return int(x) if x in ("0", "1", "2") else values[x]
        if self.op == "atom":
            return value(self.a)
        x, y = value(self.a), value(self.b)
        return {
            "+": lambda: x + y,
            "-": lambda: x - y,
            "*": lambda: x * y,
            "min": lambda: min(x, y),
            "max": lambda: max(x, y),
        }[self.op]()


def expression_pool():
    atoms = [Expr("atom", a) for a in ATOMS]
    compound = []
    for op in OPS:
        for a, b in combinations(ATOMS, 2):
            compound.append(Expr(op, a, b))
            if op == "-":
                compound.append(Expr(op, b, a))
    return atoms + compound


def run_expression_search(*, holdout_per_size: int = 120,
                          max_candidates: int = 1500):
    if not 1 <= holdout_per_size <= 500 or not 1 <= max_candidates <= 3000:
        raise ValueError("bounded experiment only")
    train = [graph_metrics(n, edges) for n in range(1, 6)
             for _, edges in graphs(n)]
    holdout = [(n, edges, graph_metrics(n, edges)) for n in (6, 7)
               for seed in (1733, 1847)
               for _, edges in graphs(n, limit=holdout_per_size, seed=seed)]
    expressions = expression_pool()
    signatures = {}
    for expression in expressions:
        signature = tuple(expression.evaluate(row) for row in train)
        signatures.setdefault(signature, []).append(expression)
    candidates = []
    for signature, equivalent in signatures.items():
        if len(set(signature)) < 3:
            continue
        for a, b in combinations(equivalent, 2):
            if a.complexity + b.complexity == 0:
                continue
            if a.label == b.label:
                continue
            candidates.append((a, b))
    candidates.sort(key=lambda pair: (
        pair[0].complexity + pair[1].complexity,
        pair[0].label, pair[1].label))
    considered = candidates[:max_candidates]
    survivors = []
    rejected = []
    for a, b in considered:
        counterexample = next(((n, edges, a.evaluate(row), b.evaluate(row))
                               for n, edges, row in holdout
                               if a.evaluate(row) != b.evaluate(row)), None)
        title = f"{a.label} = {b.label}"
        if counterexample is None:
            survivors.append(title)
        else:
            n, edges, left, right = counterexample
            rejected.append({
                "conjecture": title, "n": n,
                "edges": [list(edge) for edge in edges],
                "left_value": left, "right_value": right,
            })
    return {
        "training_graphs": len(train), "holdout_graphs": len(holdout),
        "expressions_generated": len(expressions),
        "candidate_equalities_generated": len(candidates),
        "candidates_evaluated": len(considered),
        "holdout_survivors": survivors,
        "falsified_on_holdout": rejected,
        "known_identity_review": "NOT_PERFORMED",
        "novelty_verified": False, "lean_verified": False,
        "theorem_proven": False, "promoted": False,
    }
