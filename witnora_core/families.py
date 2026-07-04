"""Deterministic formula families used by examples, tests, and benchmarks."""

from __future__ import annotations

import random

from .cnf import CNFFormula


def make_blocked_clique_collapse_family(n: int) -> CNFFormula:
    """Return the blocked-clique collapse family F_n.

    Variable mapping:
    - x = 1
    - y_i = i + 1 for 1 <= i <= n

    F_n consists of the long clause ``(x or y_1 or ... or y_n)`` and the
    binary clauses ``(not x or not y_i)``. The long clause creates a clique in
    the original primal graph and is blocked on ``x``.
    """

    if n < 1:
        raise ValueError("n must be at least 1")

    long_clause = list(range(1, n + 2))
    binary_clauses = [[-1, -(i + 1)] for i in range(1, n + 1)]
    return CNFFormula.from_raw_clauses([long_clause, *binary_clauses])


def blocked_clique_collapse_family(n: int) -> CNFFormula:
    """Alias with the theorem-note naming."""

    return make_blocked_clique_collapse_family(n)


def _literal(var: int, positive: bool) -> int:
    return var if positive else -var


def _offset_formula(formula: CNFFormula, offset: int) -> list[list[int]]:
    clauses: list[list[int]] = []
    for clause in formula.clauses:
        clauses.append([
            lit + offset if lit > 0 else lit - offset
            for lit in clause
        ])
    return clauses


def random_2sat_family(n_vars: int, n_clauses: int, seed: int) -> CNFFormula:
    """Generate a deterministic random 2-CNF formula."""

    if n_vars < 1:
        raise ValueError("n_vars must be at least 1")
    if n_clauses < 0:
        raise ValueError("n_clauses must be non-negative")

    rng = random.Random(seed)
    clauses: set[tuple[int, int]] = set()
    attempts = 0
    while len(clauses) < n_clauses and attempts < n_clauses * 100 + 100:
        attempts += 1
        a, b = rng.sample(range(1, n_vars + 1), 2) if n_vars > 1 else (1, 1)
        lit_a = _literal(a, bool(rng.getrandbits(1)))
        lit_b = _literal(b, bool(rng.getrandbits(1)))
        if lit_a == -lit_b:
            continue
        clauses.add(tuple(sorted((lit_a, lit_b))))
    return CNFFormula.from_raw_clauses(clauses)


def random_3sat_family(n_vars: int, n_clauses: int, seed: int) -> CNFFormula:
    """Generate a deterministic random 3-CNF formula."""

    if n_vars < 3:
        raise ValueError("n_vars must be at least 3")
    if n_clauses < 0:
        raise ValueError("n_clauses must be non-negative")

    rng = random.Random(seed)
    clauses: set[tuple[int, int, int]] = set()
    attempts = 0
    while len(clauses) < n_clauses and attempts < n_clauses * 200 + 200:
        attempts += 1
        vars_ = rng.sample(range(1, n_vars + 1), 3)
        lits = tuple(sorted(_literal(var, bool(rng.getrandbits(1))) for var in vars_))
        if any(-lit in lits for lit in lits):
            continue
        clauses.add(lits)
    return CNFFormula.from_raw_clauses(clauses)


def bounded_treewidth_chain_family(n: int) -> CNFFormula:
    """Generate a deterministic non-2-CNF formula with small primal width.

    The first five variables are the v0 treewidth demo core. Extra variables
    are attached by signed binary links, preserving a path-like extension while
    keeping the formula deterministic.
    """

    if n < 5:
        raise ValueError("n must be at least 5")

    clauses = [
        [-3, -1],
        [-4, -3, 2],
        [-5, -4],
        [2, 3],
        [-2, 5],
        [1, 4],
    ]
    for var in range(6, n + 1):
        clauses.append([-(var - 1), var])
        clauses.append([var - 1, -var])
    return CNFFormula.from_raw_clauses(clauses)


def bce_heavy_family(n: int, num_blocked_clauses: int) -> CNFFormula:
    """Generate disjoint blocked-clique components with many BCE removals."""

    if n < 1:
        raise ValueError("n must be at least 1")
    if num_blocked_clauses < 1:
        raise ValueError("num_blocked_clauses must be at least 1")

    clauses: list[list[int]] = []
    offset = 0
    for _ in range(num_blocked_clauses):
        component = make_blocked_clique_collapse_family(n)
        clauses.extend(_offset_formula(component, offset))
        offset += n + 1
    return CNFFormula.from_raw_clauses(clauses)


def component_mixed_family(n: int) -> CNFFormula:
    """Generate independent BCE, 2-SAT, and bounded-treewidth components."""

    width = max(3, n)
    clauses: list[list[int]] = []
    clauses.extend(_offset_formula(make_blocked_clique_collapse_family(width), 0))

    two_sat_offset = width + 1
    clauses.extend(
        _offset_formula(
            CNFFormula.from_raw_clauses([[1, 2], [-1, 2], [1, -2]]),
            two_sat_offset,
        )
    )

    treewidth_offset = two_sat_offset + 2
    clauses.extend(_offset_formula(bounded_treewidth_chain_family(5), treewidth_offset))
    return CNFFormula.from_raw_clauses(clauses)


def unsat_unit_conflict_family() -> CNFFormula:
    """Generate the minimal unit contradiction."""

    return CNFFormula.from_raw_clauses([[1], [-1]])


def tautology_noise_family(n: int) -> CNFFormula:
    """Generate tautological noise plus a deterministic unit clause."""

    if n < 1:
        raise ValueError("n must be at least 1")

    clauses = [[var, -var, ((var % n) + 1)] for var in range(1, n + 1)]
    clauses.append([1])
    return CNFFormula.from_raw_clauses(clauses)
