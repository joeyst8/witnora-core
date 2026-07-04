"""Witnora-Core v0 certified collapse-path engine."""

from .cnf import CNFFormula, Clause, Literal

__all__ = ["CNFFormula", "Clause", "Literal", "solve"]


def solve(*args, **kwargs):
    from .runner import solve as _solve

    return _solve(*args, **kwargs)
