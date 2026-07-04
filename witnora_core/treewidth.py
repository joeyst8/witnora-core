"""Exact bounded-width elimination-order search for small c."""

from __future__ import annotations

from functools import lru_cache

from .primal import Graph, graph_edges


def _canonical_state(graph: Graph) -> tuple[tuple[int, ...], tuple[tuple[int, int], ...]]:
    vertices = tuple(sorted(graph))
    return vertices, tuple(graph_edges(graph))


def _eliminate(graph: Graph, var: int) -> Graph:
    new_graph: Graph = {v: set(neighs) for v, neighs in graph.items() if v != var}
    neighbors = sorted(graph[var])
    for i, a in enumerate(neighbors):
        if a not in new_graph:
            continue
        for b in neighbors[i + 1 :]:
            if b not in new_graph:
                continue
            new_graph[a].add(b)
            new_graph[b].add(a)
    for neighs in new_graph.values():
        neighs.discard(var)
    return new_graph


def find_elimination_order(graph: Graph, width_cap: int) -> list[int] | None:
    if width_cap < 0 or width_cap > 4:
        raise ValueError("Witnora-Core v0 supports c in the range 0..4")

    failed: set[tuple[tuple[int, ...], tuple[tuple[int, int], ...]]] = set()

    def search(current: Graph) -> list[int] | None:
        if not current:
            return []
        state = _canonical_state(current)
        if state in failed:
            return None
        candidates = [
            var for var in sorted(current) if len(current[var]) <= width_cap
        ]
        candidates.sort(key=lambda var: (len(current[var]), var))
        for var in candidates:
            next_graph = _eliminate(current, var)
            rest = search(next_graph)
            if rest is not None:
                return [var] + rest
        failed.add(state)
        return None

    order = search({var: set(neighs) for var, neighs in graph.items()})
    if order is None:
        return None
    width = verify_elimination_order(graph, order)
    if width is None or width > width_cap:
        return None
    return order


def verify_elimination_order(graph: Graph, order: list[int]) -> int | None:
    current: Graph = {var: set(neighs) for var, neighs in graph.items()}
    if sorted(order) != sorted(current):
        return None
    max_width = 0
    for var in order:
        if var not in current:
            return None
        degree = len(current[var])
        max_width = max(max_width, degree)
        current = _eliminate(current, var)
    if current:
        return None
    return max_width
