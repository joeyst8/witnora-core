"""Direct 2-SAT solver using Kosaraju SCC."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .certificate import StepLogger
from .cnf import CNFFormula, Clause, formula_satisfied


def _add_edge(graph: dict[int, set[int]], src: int, dst: int) -> None:
    graph[src].add(dst)
    graph.setdefault(dst, set())


def implication_graph(formula: CNFFormula) -> dict[int, set[int]]:
    graph: dict[int, set[int]] = {lit: set() for var in formula.variables for lit in (var, -var)}
    for clause in formula.clauses:
        if len(clause) == 0:
            continue
        if len(clause) == 1:
            a = clause.literals[0]
            _add_edge(graph, -a, a)
        elif len(clause) == 2:
            a, b = clause.literals
            _add_edge(graph, -a, b)
            _add_edge(graph, -b, a)
        else:
            raise ValueError("formula is not 2-CNF")
    return {node: set(sorted(neighs)) for node, neighs in sorted(graph.items())}


def _kosaraju(graph: dict[int, set[int]]) -> tuple[dict[int, int], list[list[int]]]:
    reverse: dict[int, set[int]] = {node: set() for node in graph}
    for src, dsts in graph.items():
        reverse.setdefault(src, set())
        for dst in dsts:
            reverse.setdefault(dst, set()).add(src)

    seen: set[int] = set()
    order: list[int] = []

    def dfs1(node: int) -> None:
        seen.add(node)
        for nxt in sorted(graph.get(node, ())):
            if nxt not in seen:
                dfs1(nxt)
        order.append(node)

    for node in sorted(graph):
        if node not in seen:
            dfs1(node)

    comp: dict[int, int] = {}
    components: list[list[int]] = []

    def dfs2(node: int, comp_id: int, acc: list[int]) -> None:
        comp[node] = comp_id
        acc.append(node)
        for nxt in sorted(reverse.get(node, ())):
            if nxt not in comp:
                dfs2(nxt, comp_id, acc)

    for node in reversed(order):
        if node in comp:
            continue
        acc: list[int] = []
        dfs2(node, len(components), acc)
        components.append(sorted(acc))
    return comp, components


def solve_2sat(formula: CNFFormula, logger: StepLogger | None = None) -> dict[str, Any]:
    if not formula.is_2cnf:
        raise ValueError("formula is not 2-CNF")

    if formula.contains_empty_clause:
        details = {"status": "UNSAT", "reason": "empty_clause"}
        if logger is not None:
            logger.append("2SAT_SOLVE", formula, formula, details=details)
        return {"status": "UNSAT", "assignment": {}, "details": details}

    graph = implication_graph(formula)
    comp, components = _kosaraju(graph)

    conflict_var: int | None = None
    for var in formula.variables:
        if comp[var] == comp[-var]:
            conflict_var = var
            break

    edges = sorted((src, dst) for src, dsts in graph.items() for dst in dsts)
    if conflict_var is not None:
        details = {
            "status": "UNSAT",
            "conflict_variable": conflict_var,
            "num_implication_nodes": len(graph),
            "num_implication_edges": len(edges),
            "edges": [[src, dst] for src, dst in edges],
            "sccs": components,
        }
        if logger is not None:
            logger.append("2SAT_SOLVE", formula, formula, details=details)
        return {"status": "UNSAT", "assignment": {}, "details": details}

    assignment = {var: comp[var] > comp[-var] for var in formula.variables}
    if not formula_satisfied(formula, assignment):
        assignment = {var: not value for var, value in assignment.items()}
    if not formula_satisfied(formula, assignment):
        raise AssertionError("internal 2-SAT assignment verification failed")

    details = {
        "status": "SAT",
        "num_implication_nodes": len(graph),
        "num_implication_edges": len(edges),
        "edges": [[src, dst] for src, dst in edges],
        "sccs": components,
        "assignment": {str(var): assignment[var] for var in sorted(assignment)},
    }
    if logger is not None:
        logger.append(
            "2SAT_SOLVE",
            formula,
            formula,
            details=details,
            reconstruction_data={"assignment": details["assignment"]},
        )
    return {"status": "SAT", "assignment": assignment, "details": details}
