"""Global two-vertex separator discovery by repeated articulation scans.

For a connected graph G with no articulation vertex:
    {u, v} separates G  iff  v is an articulation vertex of G - u.

The forward and reverse implications follow directly from the definition
of articulation points because G - u remains connected. This is an
established graph-theoretic reduction, not a complexity-class discovery.
Here it is used only to order G14 candidates, never to certify a CNF.
"""

from __future__ import annotations

from typing import Mapping

from .global_coupling_separator import (
    DIAGNOSTIC_ONLY,
    _parts,
    _validated_undirected_graph,
)
from .separator_structural_priority import articulation_vertices


def vertex_coupling_pairs(graph: Mapping[int, set[int]]) -> dict:
    """Enumerate *all* two-vertex cuts in connected articulation-free graphs.

    Runs one O(V+E) articulation scan per deleted vertex, plus graph
    construction and deterministic sorting. Thus O(V(V+E)+K log K), where
    K <= V(V-1)/2 is the count of output pairs.

    An input outside this domain produces no hints, not a false promise
    of completeness; the G14 caller still retains exhaustive fallback.
    """
    adjacency = _validated_undirected_graph(graph)
    report = {
        "status": DIAGNOSTIC_ONLY,
        "strategy": "DELETE_ONE_THEN_ARTICULATION",
        "vertex_count": len(adjacency),
        "articulation_scans": 0,
        "complete_for_two_vertex_cuts": False,
        "candidates": [],
        "claim_boundary": (
            "Complete graph-theoretic two-vertex-cut hints only for "
            "connected graphs with no articulation vertex; no SAT claim."
        ),
    }
    if len(adjacency) < 3 or len(_parts(adjacency)) != 1:
        return report
    if articulation_vertices(adjacency):
        return report
    report["complete_for_two_vertex_cuts"] = True
    pairs: set[tuple[int, int]] = set()
    for removed in sorted(adjacency):
        remainder = {
            vertex: neighbors - {removed}
            for vertex, neighbors in adjacency.items()
            if vertex != removed
        }
        report["articulation_scans"] += 1
        for cut in articulation_vertices(remainder):
            pairs.add((min(removed, cut), max(removed, cut)))
    report["candidates"] = [
        {"separator": list(pair)}
        for pair in sorted(pairs)
    ]
    return report


def prioritized_vertex_pairs(graph: Mapping[int, set[int]]) -> tuple[tuple[int, int], ...]:
    """Put every articulation-derived pair first and keep all other pairs."""
    preferred = [
        tuple(row["separator"]) for row in vertex_coupling_pairs(graph)["candidates"]
    ]
    seen = set(preferred)
    vertices = sorted(graph)
    return tuple(preferred + [
        (left, right)
        for index, left in enumerate(vertices)
        for right in vertices[index + 1:]
        if (left, right) not in seen
    ])
