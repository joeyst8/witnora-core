"""Proof-trace boundary-path candidates for experimental G14 separator search.

For two-variable affine rows, XOR support is the mod-2 boundary of the
original edge provenance. Replaying each indexed G5 operation lets us find
derived two-endpoint rows whose provenance is a simple path. Path interior
versus outside size is only a *balance proxy*: chords and other source edges
can destroy the proposed cut. All actual cuts require independent graph/G14
verification. No UNSAT or proof claim is accepted from this heuristic.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from typing import Any

from .g5_elimination_activity import _support

DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"


def _index(value: Any, n: int) -> int:
    if type(value) is not int or value < 0 or value >= n:
        raise ValueError("out-of-range or noninteger live G5 row index")
    return value


def _path_interior(
    edges: frozenset[int],
    original: tuple[tuple[int, int], ...],
    boundary: frozenset[int],
) -> frozenset[int] | None:
    """Validate a connected edge-simple path with the specified boundary."""
    if len(edges) < 2 or len(boundary) != 2:
        return None
    adjacency: dict[int, set[int]] = defaultdict(set)
    seen_edges: set[tuple[int, int]] = set()
    for index in edges:
        edge = original[index]
        if edge in seen_edges:
            return None  # two equation IDs may encode one graph edge
        seen_edges.add(edge)
        left, right = edge
        adjacency[left].add(right)
        adjacency[right].add(left)
    vertices = set(adjacency)
    if set(boundary) - vertices or len(edges) != len(vertices) - 1:
        return None
    if any(len(adjacency[v]) != (1 if v in boundary else 2)
           for v in vertices):
        return None
    root = next(iter(vertices))
    visited = {root}
    pending = [root]
    while pending:
        for neighbor in adjacency[pending.pop()]:
            if neighbor not in visited:
                visited.add(neighbor)
                pending.append(neighbor)
    if visited != vertices:
        return None
    return frozenset(vertices - set(boundary))


def boundary_path_candidates_from_g5(
    initial_rows: Iterable[Mapping[str, Any]],
    operations: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Replay real indexed row operations, retain provenance-path endpoints.

    Every row must initially encode an undirected two-variable edge.
    Raises ValueError on an inconsistent operation snapshot; never trusts
    the supplied 'after' support without recomputing its symmetric difference.
    """
    initial = list(initial_rows)
    original = []
    live_support = []
    universe: set[int] = set()
    for row in initial:
        support = _support(row)
        if len(support) != 2:
            raise ValueError("path signal requires binary initial XOR rows")
        edge = tuple(sorted(support))
        original.append(edge)
        live_support.append(set(support))
        universe.update(support)
    edges = tuple(original)
    provenance = [{i} for i in range(len(initial))]
    candidates: dict[tuple[int, int], dict[str, Any]] = {}
    xor_count = 0
    for op_index, operation in enumerate(operations):
        kind = operation.get("operation")
        if kind == "SWAP_ROWS":
            a = _index(operation.get("row_a"), len(initial))
            b = _index(operation.get("row_b"), len(initial))
            live_support[a], live_support[b] = live_support[b], live_support[a]
            provenance[a], provenance[b] = provenance[b], provenance[a]
            if "rows_after" in operation:
                snapshot = operation["rows_after"]
                if (not isinstance(snapshot, list)
                        or len(snapshot) != len(initial)
                        or any(_support(row) != support for row, support
                               in zip(snapshot, live_support))):
                    raise ValueError("G5 swap snapshot disagrees with live slots")
        elif kind == "ADD_ROW_XOR":
            target = _index(operation.get("target_row"), len(initial))
            source = _index(operation.get("source_row"), len(initial))
            if target == source:
                raise ValueError("self-XOR is not an indexed G5 operation")
            before = _support(operation.get("before"))
            other = _support(operation.get("source"))
            after = _support(operation.get("after"))
            if (before != live_support[target]
                    or other != live_support[source]
                    or after != before.symmetric_difference(other)):
                raise ValueError("G5 XOR snapshot disagrees with replay")
            live_support[target] = after
            provenance[target] ^= provenance[source]
            xor_count += 1
            if len(after) != 2:
                continue
            interior = _path_interior(
                frozenset(provenance[target]), edges, frozenset(after)
            )
            if interior is None:
                continue
            outside = len(universe) - 2 - len(interior)
            proxy = min(len(interior), outside)
            if proxy <= 0:
                continue
            pair = tuple(sorted(after))
            candidate = {
                "separator": pair,
                "path_interior": len(interior),
                "path_edges": len(provenance[target]),
                "balance_proxy": proxy,
                "operation_index": op_index,
            }
            if (pair not in candidates
                    or (proxy, len(provenance[target])) >
                    (candidates[pair]["balance_proxy"],
                     candidates[pair]["path_edges"])):
                candidates[pair] = candidate
        else:
            raise ValueError("unsupported G5 operation kind")
    ranked = sorted(
        candidates.values(),
        key=lambda row: (-row["balance_proxy"], -row["path_edges"],
                         row["separator"]),
    )
    return {
        "status": DIAGNOSTIC_ONLY,
        "strategy": "INDEXED_G5_PROVENANCE_BOUNDARY_PATH",
        "initial_edge_rows": len(initial),
        "xor_operations": xor_count,
        "candidates": ranked,
        "claim_boundary": (
            "Provenance path is verified from G5 snapshots; separator validity "
            "and actual balance are not inferred and require independent G14 checks."
        ),
    }
