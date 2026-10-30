"""Seeded hidden parity separators with independent full-CNF boundary audit.

Benchmark generator and oracle only; no operator promotion or theorem claim.
"""
from __future__ import annotations

from itertools import combinations
import random

from .cnf import CNFFormula
from .xor import canonical_xor_cnf_clauses


def make_hidden_separator(seed: int, *, width: int = 2,
                          cross_noise: bool = False) -> tuple[CNFFormula, dict]:
    if width not in (2, 3):
        raise ValueError("separator width must be 2 or 3")
    rng = random.Random(seed)
    boundary = tuple(range(3, 3 + width))
    left = (1, 2, 20)
    right = (10, 11, 21)
    clauses = set(canonical_xor_cnf_clauses((1, 2, *boundary), 0))
    clauses.update(canonical_xor_cnf_clauses((*boundary, 10, 11), 1))
    clauses.update(canonical_xor_cnf_clauses(left, 0))
    clauses.update(canonical_xor_cnf_clauses(right, 1))
    clauses.add(tuple(sorted((1, 20, 30))))
    clauses.add(tuple(sorted((10, 21, -31))))
    if cross_noise:
        clauses.add(tuple(sorted((20, 21, 32))))
    variables = sorted({abs(lit) for row in clauses for lit in row})
    labels = rng.sample(range(101, 401), len(variables))
    mapping = dict(zip(variables, labels))
    permuted = [[mapping[abs(lit)] if lit > 0 else -mapping[abs(lit)]
                 for lit in row] for row in clauses]
    return CNFFormula.from_raw_clauses(permuted), {
        "seed": seed, "width": width, "cross_noise": cross_noise,
        "boundary": tuple(sorted(mapping[v] for v in boundary)),
        "left_anchor": mapping[1], "right_anchor": mapping[10],
        "left_block": tuple(sorted(mapping[v] for v in (1, 2, 20))),
        "right_block": tuple(sorted(mapping[v] for v in (10, 11, 21))),
    }


def independent_parity_cut_width(supports: list[tuple[int, ...]],
                                 *, limit: int = 3) -> int | None:
    """Independent BFS oracle over equation supports; no detector reuse."""
    shared = sorted(v for v in set().union(*map(set, supports))
                    if sum(v in item for item in supports) >= 2)
    def count_parts(deleted):
        unseen = set(range(len(supports)))
        count = 0
        while unseen:
            count += 1
            queue = [unseen.pop()]
            while queue:
                i = queue.pop()
                neighbor = {j for j in unseen
                            if (set(supports[i]) - deleted)
                            & (set(supports[j]) - deleted)}
                unseen.difference_update(neighbor)
                queue.extend(neighbor)
        return count
    baseline = count_parts(set())
    for size in range(1, limit + 1):
        for cut in combinations(shared, size):
            if count_parts(set(cut)) > baseline:
                return size
    return None


def full_cnf_anchors_separated(formula: CNFFormula, cut: tuple[int, ...],
                               left_anchor: int, right_anchor: int) -> bool:
    """Independent primal-graph reachability audit after removing a cut."""
    excluded = set(cut)
    if left_anchor in excluded or right_anchor in excluded:
        return False
    neighbors: dict[int, set[int]] = {}
    for clause in formula.clauses:
        variables = {abs(lit) for lit in clause} - excluded
        for v in variables:
            neighbors.setdefault(v, set()).update(variables - {v})
    reached = {left_anchor}
    queue = [left_anchor]
    while queue:
        for nxt in neighbors.get(queue.pop(), set()) - reached:
            reached.add(nxt)
            queue.append(nxt)
    return right_anchor not in reached
