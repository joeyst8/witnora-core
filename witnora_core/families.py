"""Deterministic formula families used by examples and regression tests."""

from __future__ import annotations

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
