"""Exact two-edge-cut boundary candidates for G14 separator discovery.

This is a deliberately polynomial but brute-force graph prototype:
enumerate unordered pairs of edges, test whether deleting exactly those
edges splits a connected graph in two, and inspect the endpoint boundary
of each side. Any reported vertex pair is *separately* validated by
deleting those two vertices from the original graph.

These are discovery hints only. They cannot certify CNF satisfiability,
G14 family membership, or a G5 proof. Cost is O(E^2 (V + E));
the standard graph-connectivity literature offers faster algorithms.
"""

from __future__ import annotations

from itertools import combinations
from typing import Mapping

DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"


def _validated_undirected_graph(graph: Mapping[int, set[int]]) -> dict[int, set[int]]:
    adjacency = {v: set(neighbors) for v, neighbors in graph.items()}
    for vertex, neighbors in adjacency.items():
        if vertex in neighbors:
            raise ValueError("graph contains a self-loop")
        for other in neighbors:
            if other not in adjacency or vertex not in adjacency[other]:
                raise ValueError("graph edges must be symmetric and have known endpoints")
    return adjacency


def _parts(
    graph: Mapping[int, set[int]],
    *,
    omit_vertices: frozenset[int] = frozenset(),
    omit_edges: frozenset[tuple[int, int]] = frozenset(),
) -> list[tuple[int, ...]]:
    seen: set[int] = set()
    result: list[tuple[int, ...]] = []
    for root in sorted(set(graph) - omit_vertices):
        if root in seen:
            continue
        seen.add(root)
        stack = [root]
        part: list[int] = []
        while stack:
            vertex = stack.pop()
            part.append(vertex)
            for neighbor in sorted(graph[vertex]):
                if neighbor in omit_vertices or neighbor in seen:
                    continue
                edge = (min(vertex, neighbor), max(vertex, neighbor))
                if edge in omit_edges:
                    continue
                seen.add(neighbor)
                stack.append(neighbor)
        result.append(tuple(sorted(part)))
    return result


def two_edge_cut_boundary_pairs(graph: Mapping[int, set[int]]) -> dict:
    """Find validated size-two vertex separators witnessed by two-edge cuts.

    The input must be a simple symmetric undirected graph. Disconnected
    graphs are deliberately skipped: the operator only studies a new
    split caused by removal from an originally connected primal graph.
    Candidate ordering is deterministic and favours balanced residuals.
    """
    adjacency = _validated_undirected_graph(graph)
    edges = sorted(
        (left, right)
        for left in adjacency
        for right in adjacency[left]
        if left < right
    )
    report = {
        "status": DIAGNOSTIC_ONLY,
        "strategy": "TWO_EDGE_CUT_BOUNDARY",
        "vertex_count": len(adjacency),
        "edge_count": len(edges),
        "edge_pair_checks": 0,
        "candidates": [],
        "claim_boundary": (
            "Exact graph-cut candidates, not G14 recognition, a SAT answer, "
            "or a complexity-theory result."
        ),
    }
    if not adjacency or len(_parts(adjacency)) != 1:
        return report

    candidates: dict[tuple[int, int], dict] = {}
    for first, second in combinations(edges, 2):
        report["edge_pair_checks"] += 1
        pieces = _parts(adjacency, omit_edges=frozenset((first, second)))
        if len(pieces) != 2:
            continue
        side = set(pieces[0])
        # Demand that *both* deleted edges cross the resulting partition:
        # neither edge may be an incidental within-component deletion.
        if not all((u in side) != (v in side) for u, v in (first, second)):
            continue
        for part in pieces:
            vertices = set(part)
            boundary = tuple(sorted(
                vertex for edge in (first, second)
                for vertex in edge if vertex in vertices
            ))
            if len(boundary) != 2 or boundary[0] == boundary[1]:
                continue
            if boundary in candidates:
                continue
            residual = _parts(adjacency, omit_vertices=frozenset(boundary))
            if len(residual) <= 1:
                continue
            candidates[boundary] = {
                "separator": list(boundary),
                "cut_edges": [list(first), list(second)],
                "edge_split_sizes": [len(part) for part in pieces],
                "residual_component_sizes": sorted(len(p) for p in residual),
            }
    report["candidates"] = sorted(
        candidates.values(),
        key=lambda item: (
            -min(item["residual_component_sizes"]),
            max(item["residual_component_sizes"]),
            tuple(item["separator"]),
        ),
    )
    return report


def prioritized_global_pairs(graph: Mapping[int, set[int]]) -> tuple[tuple[int, int], ...]:
    """Prefer exact graph-cut witnesses, then retain exhaustive pair fallback."""
    vertices = sorted(graph)
    preferred = [
        tuple(candidate["separator"])
        for candidate in two_edge_cut_boundary_pairs(graph)["candidates"]
    ]
    already = set(preferred)
    return tuple(preferred + [
        pair for pair in combinations(vertices, 2) if pair not in already
    ])
