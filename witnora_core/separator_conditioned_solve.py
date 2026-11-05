"""Experimental SAT by conditioning a verified primal-graph separator.

No trusted proof or performance claim. SAT/UNSAT results are checked against
independent solvers in finite experiments. Uses PySAT only at execution time.
"""
from __future__ import annotations

from itertools import product

from .cnf import CNFFormula
from .multicut_parity_separator import bounded_parity_separators


def primal_components(formula: CNFFormula, removed=()) -> list[tuple[int, ...]]:
    removed = set(removed)
    graph: dict[int, set[int]] = {}
    for clause in formula.clauses:
        variables = {abs(lit) for lit in clause} - removed
        for var in variables:
            graph.setdefault(var, set()).update(variables - {var})
    remaining = set(graph)
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        seen = {start}
        frontier = [start]
        while frontier:
            for neighbor in graph[frontier.pop()] & remaining:
                remaining.remove(neighbor)
                seen.add(neighbor)
                frontier.append(neighbor)
        components.append(tuple(sorted(seen)))
    return sorted(components)


def restrict_formula(formula: CNFFormula, assignment: dict[int, bool]) -> CNFFormula:
    rows = []
    for clause in formula.clauses:
        retained = []
        satisfied = False
        for lit in clause:
            value = assignment.get(abs(lit))
            if value is None:
                retained.append(lit)
            elif value == (lit > 0):
                satisfied = True
                break
        if not satisfied:
            rows.append(retained)
    return CNFFormula.from_raw_clauses(rows)


def split_residual(formula: CNFFormula) -> list[CNFFormula]:
    """Partition clauses by their connected primal-variable components."""
    if formula.contains_empty_clause:
        return [formula]
    groups = primal_components(formula)
    if not groups:
        return []
    owner = {v: index for index, group in enumerate(groups) for v in group}
    chunks = [[] for _ in groups]
    for clause in formula.clauses:
        chunks[owner[abs(clause.literals[0])]].append(clause)
    return [CNFFormula(rows) for rows in chunks]


def solve_conditioned(formula: CNFFormula, *, max_cut: int = 3) -> dict:
    """Enumerate at most 2^3 boundary assignments; fallback when no full cut."""
    from pysat.solvers import Glucose3

    def sat(candidate: CNFFormula) -> bool:
        with Glucose3(bootstrap_with=candidate.to_clause_lists()) as solver:
            return bool(solver.solve())

    proposed = bounded_parity_separators(formula, max_cut=max_cut)
    selected = None
    for candidate in proposed["candidate_cuts"]:
        cut = tuple(candidate["variables"])
        if len(primal_components(formula, cut)) > len(primal_components(formula)):
            selected = cut
            break
    if selected is None:
        return {"satisfiable": sat(formula), "mode": "direct_fallback",
                "cut": [], "assignments_examined": 0, "component_calls": 0,
                "trusted": False, "lean_verified": False, "promoted": False}
    calls = 0
    examined = 0
    for values in product((False, True), repeat=len(selected)):
        examined += 1
        residual = restrict_formula(formula, dict(zip(selected, values)))
        if residual.contains_empty_clause:
            continue
        components = split_residual(residual)
        all_sat = True
        for component in components:
            calls += 1
            if not sat(component):
                all_sat = False
                break
        if all_sat:
            return {"satisfiable": True, "mode": "conditioned",
                    "cut": list(selected), "assignments_examined": examined,
                    "component_calls": calls, "trusted": False,
                    "lean_verified": False, "promoted": False}
    return {"satisfiable": False, "mode": "conditioned",
            "cut": list(selected), "assignments_examined": examined,
            "component_calls": calls, "trusted": False,
            "lean_verified": False, "promoted": False}
