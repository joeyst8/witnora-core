"""Primal graph construction for CNF formulas."""

from __future__ import annotations

from itertools import combinations

from .cnf import CNFFormula

Graph = dict[int, set[int]]


def primal_graph(formula: CNFFormula, *, backend: str = "python") -> Graph:
    if backend == "rust":
        from witnora_ve import primal_graph_native
        variables, edges = primal_graph_native(formula.to_clause_lists())
        graph: Graph = {var: set() for var in variables}
        for a, b in edges:
            graph[a].add(b)
            graph[b].add(a)
        return graph
    if backend != "python":
        raise ValueError("unknown primal graph backend")
    graph: Graph = {var: set() for var in formula.variables}
    for clause in formula.clauses:
        vars_in_clause = clause.variables
        for a, b in combinations(vars_in_clause, 2):
            graph.setdefault(a, set()).add(b)
            graph.setdefault(b, set()).add(a)
    return {var: set(sorted(neigh)) for var, neigh in sorted(graph.items())}


def graph_edges(graph: Graph) -> list[tuple[int, int]]:
    edges: list[tuple[int, int]] = []
    for a, neighs in graph.items():
        for b in neighs:
            if a < b:
                edges.append((a, b))
    return sorted(edges)


def clone_graph(graph: Graph) -> Graph:
    return {var: set(neighs) for var, neighs in graph.items()}
