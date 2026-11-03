"""Reproducible, scope-aware variable-elimination order experiments.

This measures GRAPH elimination fill, not tensor contraction, SAT run time,
or exact treewidth. No assignment enumeration is used.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from heapq import nsmallest


@dataclass(frozen=True)
class OrderResult:
    mode: str
    induced_width: int
    added_fill_edges: int
    order: tuple[int, ...]


def elimination_order(
    scopes: list[set[int]], nvars: int, *,
    nsource: int,
    mode: str = "min_degree",
    beam: int = 8,
) -> OrderResult:
    """Greedy elimination with optional source/aux staging or limited min-fill.

    - min_degree: smallest active neighbor count.
    - source_first: source bits first, then auxiliary bits.
    - aux_first: auxiliary bits first, then source bits.
    - beam_fill: among the beam least-degree candidates, prefer the
      fewest missing neighbor-neighbor edges. It is a *heuristic*.
    """
    if nvars < 0 or not 0 <= nsource <= nvars:
        raise ValueError("invalid source/total variable counts")
    if mode not in ("min_degree", "source_first", "aux_first", "beam_fill"):
        raise ValueError("unknown order mode")
    if beam < 1:
        raise ValueError("beam must be positive")
    graph: dict[int, set[int]] = {v: set() for v in range(1, nvars + 1)}
    for scope in scopes:
        if any(v < 1 or v > nvars for v in scope):
            raise ValueError("factor variable outside declared domain")
        for v in scope:
            graph[v].update(scope - {v})

    active = set(graph)
    order: list[int] = []
    width = added = 0
    while active:
        neighbors_cache = {v: graph[v] & active for v in active}

        def degree_key(v: int) -> tuple[int, int]:
            return len(neighbors_cache[v]), v

        if mode == "source_first":
            chosen = min(active, key=lambda v: (v > nsource, *degree_key(v)))
        elif mode == "aux_first":
            chosen = min(active, key=lambda v: (v <= nsource, *degree_key(v)))
        elif mode == "beam_fill":
            candidates = nsmallest(beam, active, key=degree_key)

            def fill_key(v: int) -> tuple[int, int, int]:
                ns = neighbors_cache[v]
                missing = sum(len(ns - graph[u] - {u}) for u in ns) // 2
                return missing, len(ns), v

            chosen = min(candidates, key=fill_key)
        else:
            chosen = min(active, key=degree_key)

        ns = neighbors_cache[chosen]
        width = max(width, len(ns))
        # Count undirected missing neighbor pairs before adding any edges.
        added += sum(len(ns - graph[u] - {u}) for u in ns) // 2
        for u in sorted(ns):
            graph[u].update(ns - {u})
            graph[u].discard(chosen)
        active.remove(chosen)
        order.append(chosen)
    return OrderResult(mode, width, added, tuple(order))


def replay_elimination_width(
    scopes: list[set[int]], nvars: int, order: tuple[int, ...],
) -> int:
    """Independent replay of a proposed complete order (no greedy choices)."""
    if len(order) != nvars or set(order) != set(range(1, nvars + 1)):
        raise ValueError("order must be a permutation of all variable IDs")
    graph: dict[int, set[int]] = {v: set() for v in range(1, nvars + 1)}
    for scope in scopes:
        if any(v < 1 or v > nvars for v in scope):
            raise ValueError("invalid factor scope")
        for u, v in combinations(sorted(scope), 2):
            graph[u].add(v)
            graph[v].add(u)
    width = 0
    for v in order:
        ns = graph[v]
        width = max(width, len(ns))
        for u in ns:
            graph[u].update(ns - {u})
            graph[u].discard(v)
        graph[v] = set()
    return width
