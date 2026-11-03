"""W-CRC-009: source-bound sufficient structural independence certificate.

If no source primal-graph component touches both groups A and B,
the signed CNF factors across those components. A checked satisfying
assignment establishes that the conditional distribution on models
exists; then A and B are independent under that distribution.

Graph connectivity is only a *sufficient* test: a connected source
may still be semantically independent. The checker must not call a
failed structural test "dependent".
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from witnora_core.crc_boundary import _normalized_clauses


@dataclass(frozen=True)
class StructuralIndependenceAudit:
    separated: bool
    source_components: int
    clauses_checked: int
    witness_accepted: bool = True


def audit_structural_source_independence(
    source_clauses: Iterable[Iterable[int]],
    boundary_variables: tuple[int, ...],
    left_group: tuple[int, ...],
    right_group: tuple[int, ...],
    satisfying_assignment: int,
) -> StructuralIndependenceAudit | None:
    """Return a sufficient source-relative independence certificate.

    None means the offered assignment was not a source model (or the
    source has an empty clause). A False result only means the primal
    component test was inconclusive, never that dependence is proven.
    """
    if not isinstance(satisfying_assignment, int) or satisfying_assignment < 0:
        raise ValueError("invalid Boolean assignment mask")
    bset = set(boundary_variables)
    if len(bset) != len(boundary_variables):
        raise ValueError("duplicate boundary variable")
    boundary_mask = 0
    for v in boundary_variables:
        if not isinstance(v, int) or v <= 0 or v > 256:
            raise ValueError("boundary IDs must be in 1..256")
        boundary_mask |= 1 << (v - 1)
    if satisfying_assignment & ~boundary_mask:
        raise ValueError("witness sets non-boundary variable")
    for group in (left_group, right_group):
        if not group or len(set(group)) != len(group):
            raise ValueError("groups must be nonempty and duplicate-free")
        if any(v not in bset for v in group):
            raise ValueError("group references non-boundary variable")
    if set(left_group) & set(right_group):
        raise ValueError("groups overlap")

    clauses = _normalized_clauses(source_clauses, boundary_variables)
    if clauses is None:
        return None
    # A signed clause is violated iff every positive literal is false
    # and every negative literal is true.
    if any((satisfying_assignment & zeros) == 0 and
           (satisfying_assignment & ones) == ones
           for zeros, ones in clauses):
        return None

    parent = {v: v for v in boundary_variables}

    def root(v):
        while parent[v] != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v

    def union(a, b):
        ra, rb = root(a), root(b)
        if ra != rb:
            parent[rb] = ra

    for zeros, ones in clauses:
        scope = zeros | ones
        vertices = tuple(v for v in boundary_variables
                         if scope & (1 << (v - 1)))
        if not vertices:
            continue
        for v in vertices[1:]:
            union(vertices[0], v)

    left_components = {root(v) for v in left_group}
    right_components = {root(v) for v in right_group}
    separated = not bool(left_components & right_components)
    count = len({root(v) for v in boundary_variables})
    return StructuralIndependenceAudit(
        separated, count, len(clauses))
