"""Resolution/RUP proof extraction for 2-SAT SCC contradictions."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable

from .cnf import Clause, CNFFormula, has_tautology

ClauseTuple = tuple[int, ...]


@dataclass(frozen=True)
class ImplicationEdgeProof:
    source: int
    target: int
    clause: ClauseTuple

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "target": self.target,
            "clause": list(self.clause),
        }


@dataclass(frozen=True)
class TwoSatSCCProof:
    variable: int
    path_pos_to_neg: tuple[ImplicationEdgeProof, ...]
    path_neg_to_pos: tuple[ImplicationEdgeProof, ...]
    derived_clauses: tuple[ClauseTuple, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "variable": self.variable,
            "path_pos_to_neg": [edge.to_dict() for edge in self.path_pos_to_neg],
            "path_neg_to_pos": [edge.to_dict() for edge in self.path_neg_to_pos],
            "derived_clauses": [list(clause) for clause in self.derived_clauses],
        }


def _canonical_clause(literals: Iterable[int]) -> ClauseTuple:
    return Clause(literals).literals


def _source_clause_for_edge(source: int, target: int) -> ClauseTuple:
    return _canonical_clause((-source, target))


def _normalise_formula(
    formula_or_clauses: CNFFormula | Iterable[Iterable[int]],
) -> tuple[ClauseTuple, ...]:
    if isinstance(formula_or_clauses, CNFFormula):
        clauses = [clause.literals for clause in formula_or_clauses.clauses]
    else:
        clauses = [_canonical_clause(clause) for clause in formula_or_clauses]
    if any(len(clause) > 2 for clause in clauses):
        raise ValueError("2-SAT SCC proof extraction requires clauses of width <= 2")
    return tuple(sorted(set(clauses)))


def implication_graph_with_sources(
    formula_or_clauses: CNFFormula | Iterable[Iterable[int]],
) -> tuple[dict[int, set[int]], dict[tuple[int, int], ClauseTuple]]:
    clauses = _normalise_formula(formula_or_clauses)
    variables = sorted({abs(lit) for clause in clauses for lit in clause})
    graph: dict[int, set[int]] = {lit: set() for var in variables for lit in (var, -var)}
    sources: dict[tuple[int, int], ClauseTuple] = {}
    for clause in clauses:
        if len(clause) == 0:
            continue
        if len(clause) == 1:
            lit = clause[0]
            edge = (-lit, lit)
            graph.setdefault(edge[0], set()).add(edge[1])
            graph.setdefault(edge[1], set())
            sources[edge] = clause
            continue
        a, b = clause
        for edge in [(-a, b), (-b, a)]:
            graph.setdefault(edge[0], set()).add(edge[1])
            graph.setdefault(edge[1], set())
            sources[edge] = clause
    return graph, sources


def _find_path_nodes(graph: dict[int, set[int]], start: int, target: int) -> list[int] | None:
    queue: deque[int] = deque([start])
    parent: dict[int, int | None] = {start: None}
    while queue:
        node = queue.popleft()
        if node == target:
            path: list[int] = []
            cursor: int | None = node
            while cursor is not None:
                path.append(cursor)
                cursor = parent[cursor]
            return list(reversed(path))
        for nxt in sorted(graph.get(node, ())):
            if nxt not in parent:
                parent[nxt] = node
                queue.append(nxt)
    return None


def _path_edges(
    nodes: list[int],
    sources: dict[tuple[int, int], ClauseTuple],
) -> tuple[ImplicationEdgeProof, ...]:
    edges: list[ImplicationEdgeProof] = []
    for source, target in zip(nodes, nodes[1:]):
        clause = sources.get((source, target))
        if clause is None:
            expected = _source_clause_for_edge(source, target)
            raise ValueError(
                f"implication edge {source}->{target} has no source clause {expected}"
            )
        edges.append(ImplicationEdgeProof(source, target, clause))
    if not edges:
        raise ValueError("2-SAT SCC path must contain at least one implication edge")
    return tuple(edges)


def _resolve_for_path(current: ClauseTuple, edge: ImplicationEdgeProof) -> ClauseTuple:
    pivot = edge.source
    if pivot not in current:
        raise ValueError("path resolution pivot missing from current clause")
    if -pivot not in edge.clause:
        raise ValueError("path resolution pivot complement missing from edge clause")
    raw = [lit for lit in current if lit != pivot] + [
        lit for lit in edge.clause if lit != -pivot
    ]
    if has_tautology(raw):
        raise ValueError("path resolution generated tautological intermediate clause")
    return _canonical_clause(raw)


def _derive_path_clauses(path: tuple[ImplicationEdgeProof, ...]) -> tuple[ClauseTuple, ...]:
    current = path[0].clause
    if len(path) == 1:
        return (current,)
    derived: list[ClauseTuple] = []
    for edge in path[1:]:
        current = _resolve_for_path(current, edge)
        derived.append(current)
    return tuple(derived)


def build_2sat_scc_proof(
    formula_or_clauses: CNFFormula | Iterable[Iterable[int]],
    conflict_variable: int | None = None,
) -> TwoSatSCCProof:
    graph, sources = implication_graph_with_sources(formula_or_clauses)
    variables = sorted({abs(lit) for lit in graph})
    candidates = [conflict_variable] if conflict_variable is not None else variables
    for raw_var in candidates:
        var = int(raw_var)
        if var <= 0:
            continue
        pos_to_neg_nodes = _find_path_nodes(graph, var, -var)
        neg_to_pos_nodes = _find_path_nodes(graph, -var, var)
        if pos_to_neg_nodes is None or neg_to_pos_nodes is None:
            continue
        pos_to_neg = _path_edges(pos_to_neg_nodes, sources)
        neg_to_pos = _path_edges(neg_to_pos_nodes, sources)
        derived = _derive_path_clauses(pos_to_neg) + _derive_path_clauses(neg_to_pos)
        expected_units = {_canonical_clause((-var,)), _canonical_clause((var,))}
        if set(derived[-2:]) != expected_units:
            raise ValueError("2-SAT SCC paths did not derive complementary units")
        return TwoSatSCCProof(
            variable=var,
            path_pos_to_neg=pos_to_neg,
            path_neg_to_pos=neg_to_pos,
            derived_clauses=derived,
        )
    raise ValueError("no mutually reachable variable/negation pair found")
