"""W-CRC-011: bounded exact minimum primal-graph vertex separator.

Find a minimum cut separating source variable groups A/B, excluding
their own vertices, using vertex-splitting max flow. The small
separator is passed to W-CRC-010 for a signed-source-checked
conditional-independence certificate. This is an established graph
algorithm, not a new SAT algorithm or an unconditional independence
claim. All search and edge budgets fail closed.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from itertools import combinations
from typing import Iterable

from witnora_core.crc_boundary import _mask, _normalized_clauses
from witnora_core.crc_conditional_independence import (
    ConditionalStructuralAudit, audit_conditioned_source_independence,
)


@dataclass(frozen=True)
class DiscoveredSeparator:
    separator: tuple[int, ...]
    minimum_size: int
    primal_edges: int
    augmentations: int
    conditional_certificate: ConditionalStructuralAudit


def discover_source_separator(
    source_clauses: Iterable[Iterable[int]],
    boundary_variables: tuple[int, ...],
    left_group: tuple[int, ...],
    right_group: tuple[int, ...],
    satisfying_assignment: int,
    *,
    max_separator_size: int = 4,
    max_primal_edges: int = 10000,
) -> DiscoveredSeparator | None:
    """Return a verified minimum A-B primal vertex cut within budgets.

    A result certifies independence only *conditional on the discovered
    cut variables fixed to values from the offered source model*.
    None means no admitted cut, resource cap, or invalid source model.
    """
    if not isinstance(max_separator_size, int) or max_separator_size < 0:
        raise ValueError("max_separator_size must be nonnegative")
    if not isinstance(max_primal_edges, int) or max_primal_edges < 0:
        raise ValueError("max_primal_edges must be nonnegative")
    bmask = _mask(boundary_variables)
    if (not isinstance(satisfying_assignment, int) or
        satisfying_assignment < 0 or
        satisfying_assignment & ~bmask):
        raise ValueError("invalid full assignment mask")
    left, right = set(left_group), set(right_group)
    if (not left or not right or len(left) != len(left_group) or
        len(right) != len(right_group) or left & right or
        (left | right) - set(boundary_variables)):
        raise ValueError("invalid group membership")

    source = tuple(tuple(c) for c in source_clauses)
    normalized = _normalized_clauses(source, boundary_variables)
    if normalized is None:
        return None
    if any((satisfying_assignment & z) == 0 and
           (satisfying_assignment & o) == o
           for z, o in normalized):
        return None

    graph = {v: set() for v in boundary_variables}
    edges = set()
    for zeros, ones in normalized:
        scope = zeros | ones
        vertices = []
        while scope:
            bit = scope & -scope
            vertices.append(bit.bit_length())
            scope ^= bit
        for u, v in combinations(vertices, 2):
            edge = (min(u, v), max(u, v))
            if edge in edges:
                continue
            edges.add(edge)
            if len(edges) > max_primal_edges:
                return None
            graph[u].add(v)
            graph[v].add(u)

    n = len(boundary_variables)
    pos = {v: i for i, v in enumerate(boundary_variables)}
    src, dst, infinite = 2 * n, 2 * n + 1, n + 1
    residual = [dict() for _ in range(2 * n + 2)]

    def add_arc(u, v, capacity):
        residual[u][v] = residual[u].get(v, 0) + capacity
        residual[v].setdefault(u, 0)

    for v in boundary_variables:
        i = pos[v]
        add_arc(2 * i, 2 * i + 1,
                infinite if v in left or v in right else 1)
    for u, v in sorted(edges):
        a, b = pos[u], pos[v]
        add_arc(2 * a + 1, 2 * b, infinite)
        add_arc(2 * b + 1, 2 * a, infinite)
    for v in sorted(left):
        add_arc(src, 2 * pos[v], infinite)
    for v in sorted(right):
        add_arc(2 * pos[v] + 1, dst, infinite)

    flow, augmentations = 0, 0
    while True:
        parent = {src: -1}
        search = deque([src])
        while search and dst not in parent:
            at = search.popleft()
            for other, capacity in residual[at].items():
                if capacity > 0 and other not in parent:
                    parent[other] = at
                    search.append(other)
        if dst not in parent:
            reachable = set(parent)
            break
        increment = infinite
        at = dst
        while at != src:
            prev = parent[at]
            increment = min(increment, residual[prev][at])
            at = prev
        at = dst
        while at != src:
            prev = parent[at]
            residual[prev][at] -= increment
            residual[at][prev] = residual[at].get(prev, 0) + increment
            at = prev
        flow += increment
        augmentations += 1
        if flow > max_separator_size:
            return None

    separator = tuple(sorted(
        v for v in boundary_variables
        if 2 * pos[v] in reachable and
           2 * pos[v] + 1 not in reachable
    ))
    if len(separator) != flow or (set(separator) & (left | right)):
        raise AssertionError("minimum vertex cut extraction invariant")
    # Independent primal-graph reachability check, not a flow residual test.
    allowed = set(boundary_variables) - set(separator)
    seen = set(left)
    queue = deque(sorted(left))
    while queue:
        at = queue.popleft()
        for other in graph[at] & allowed:
            if other not in seen:
                seen.add(other)
                queue.append(other)
    if seen & right:
        raise AssertionError("derived cut does not separate groups")

    certificate = audit_conditioned_source_independence(
        source, boundary_variables, left_group, right_group,
        separator, satisfying_assignment)
    if (certificate is None or
        not certificate.separated_after_conditioning):
        raise AssertionError("source-relative conditional certificate mismatch")
    return DiscoveredSeparator(
        separator, flow, len(edges), augmentations, certificate)
