"""Subsumption transformation."""

from __future__ import annotations

from .cnf import CNFFormula, Clause


def find_first_subsumption(formula: CNFFormula, *,
                           backend: str = "python") -> tuple[Clause, Clause] | None:
    if backend == "rust":
        from .cnf_rust import first_subsumption_in_rust
        return first_subsumption_in_rust(formula)
    if backend != "python":
        raise ValueError("unknown subsumption backend")
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
