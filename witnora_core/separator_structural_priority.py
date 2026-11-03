"""Fast, deterministic primal-graph separator candidates for TC-063.

Articulation vertices are found with iterative DFS low-link bookkeeping.
They are only *hints*: the G14/SAT recognizer must still validate every
candidate and must retain an exhaustive fallback. No completeness or
complexity-class claim rests on this heuristic.
"""

from __future__ import annotations

from collections.abc import Mapping


def articulation_vertices(graph: Mapping[int, set[int]]) -> tuple[int, ...]:
    """Find graph articulation vertices by a linear-time O(V+E) DFS.

    Final sorting of the returned articulation set costs O(k log k),
    where k is the number of cuts. Iterative DFS avoids recursion limits.
    All graph neighbors must themselves be keys and edges be symmetric,
    as they are in Witnora's primal graph.
    """
    discovery: dict[int, int] = {}
    low: dict[int, int] = {}
    parent: dict[int, int | None] = {}
    children: dict[int, int] = {}
    cut: set[int] = set()
    clock = 0
    # The low-link scan needs no neighbor ordering; sorting is only used
    # for the final, deterministic candidate ranking.
    adjacency = {v: tuple(graph[v]) for v in graph}

    for root in graph:
        if root in discovery:
            continue
        parent[root] = None
        children[root] = 0
        discovery[root] = low[root] = clock
        clock += 1
        stack = [(root, iter(adjacency[root]))]
        while stack:
            vertex, neighbors = stack[-1]
            try:
                neighbor = next(neighbors)
            except StopIteration:
                stack.pop()
                ancestor = parent[vertex]
                if ancestor is None:
                    if children[vertex] > 1:
                        cut.add(vertex)
                else:
                    low[ancestor] = min(low[ancestor], low[vertex])
                    if parent[ancestor] is not None and low[vertex] >= discovery[ancestor]:
                        cut.add(ancestor)
                continue

            if neighbor == parent[vertex]:
                continue
            if neighbor in discovery:
                low[vertex] = min(low[vertex], discovery[neighbor])
                continue
            parent[neighbor] = vertex
            children[neighbor] = 0
            children[vertex] += 1
            discovery[neighbor] = low[neighbor] = clock
            clock += 1
            stack.append((neighbor, iter(adjacency[neighbor])))

    return tuple(sorted(cut))


def prioritized_singletons(graph: Mapping[int, set[int]]) -> tuple[int, ...]:
    """Try structurally certified cuts first, but include every variable once.

    Degree is only a cheap tie-breaker. Any acceptance claim must come
    from the existing exact affine-component and G14 certificate checks.
    """
    cuts = set(articulation_vertices(graph))
    first = sorted(cuts, key=lambda v: (-len(graph[v]), v))
    remainder = sorted(v for v in graph if v not in cuts)
    return tuple(first + remainder)
