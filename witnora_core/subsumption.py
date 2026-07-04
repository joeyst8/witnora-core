"""Subsumption transformation."""

from __future__ import annotations

from .cnf import CNFFormula, Clause


def find_first_subsumption(formula: CNFFormula) -> tuple[Clause, Clause] | None:
    clauses = list(formula.clauses)
    for subsumer in clauses:
        subsumer_set = set(subsumer.literals)
        for removed in clauses:
            if subsumer == removed:
                continue
            if len(subsumer) > len(removed):
                continue
            if len(subsumer) == len(removed):
                continue
            if subsumer_set.issubset(removed.literals):
                return subsumer, removed
    return None
