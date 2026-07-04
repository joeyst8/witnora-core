"""Witnora-Core v0.8.4 certified collapse-path engine."""

from .cnf import CNFFormula, Clause, Literal
from .families import make_blocked_clique_collapse_family

__all__ = [
    "CNFFormula",
    "Clause",
    "Literal",
    "make_blocked_clique_collapse_family",
    "solve",
]


def solve(*args, **kwargs):
    from .runner import solve as _solve

    return _solve(*args, **kwargs)
