"""W-CRC-015: exact VE with incremental factor incidence and heap scores.

Mathematics and fail-closed caps are identical to W-CRC-014. Unlike
the reference implementation, each elimination only rescored variables
touched by factors removed or introduced at that step. Versioned heap
entries safely discard stale scores. No general SAT speedup is claimed.
"""
from __future__ import annotations

from dataclasses import dataclass
import heapq
from typing import Iterable

from witnora_core.crc_boundary import _mask
from witnora_core.crc_variable_elimination import VariableEliminationCount


@dataclass(frozen=True)
class _IndexedFactor:
    scope: tuple[int, ...]
    table: tuple[int, ...]


def count_component_by_indexed_elimination(
    violation_clauses: Iterable[tuple[int, int]],
    component_variables: tuple[int, ...],
    *,
    max_factor_variables: int = 6,
    max_operations: int = 1000000,
) -> VariableEliminationCount | None:
    """Exact sum-product VE with versioned min-scope elimination heap."""
    if (not isinstance(max_factor_variables, int) or
        not 1 <= max_factor_variables <= 16 or
        not isinstance(max_operations, int) or max_operations < 1):
        raise ValueError("invalid VE width or operation budget")
    if len(component_variables) != len(set(component_variables)):
        raise ValueError("duplicate component variable")
    allowed = _mask(component_variables)
    clauses = tuple(violation_clauses)
    factors: dict[int, _IndexedFactor] = {}
    incidence = {v: set() for v in component_variables}
    next_id, operations, maximum_width = 0, 0, 0
    for zeros, ones in clauses:
        if (not isinstance(zeros, int) or not isinstance(ones, int)
            or zeros < 0 or ones < 0 or (zeros & ones)
            or (zeros | ones) & ~allowed):
            raise ValueError("invalid violation masks")
        if not (zeros | ones):
            return VariableEliminationCount(0, operations, maximum_width, 0)
        scope = tuple(v for v in component_variables
                      if (zeros | ones) & (1 << (v - 1)))
        width = len(scope)
        if width > max_factor_variables:
            return None
        maximum_width = max(maximum_width, width)
        entries = 1 << width
        if entries > max_operations - operations:
            return None
        operations += entries
        values = []
        for packed in range(entries):
            assignment = 0
            for i, v in enumerate(scope):
                if packed & (1 << i):
                    assignment |= 1 << (v - 1)
            violated = (assignment & zeros) == 0 and (
                assignment & ones) == ones
            values.append(0 if violated else 1)
        factors[next_id] = _IndexedFactor(scope, tuple(values))
        for v in scope:
            incidence[v].add(next_id)
        next_id += 1

    active = set(component_variables)
    versions = {v: 0 for v in component_variables}
    heap = []

    def push_score(v):
        relevant = incidence[v]
        union = {v}
        for fid in relevant:
            union.update(factors[fid].scope)
        heapq.heappush(heap, (len(union), len(relevant), v, versions[v]))

    for v in sorted(active):
        push_score(v)

    constant = 1
    for eliminated in range(len(component_variables)):
        while heap:
            width, _count, v, stamp = heapq.heappop(heap)
            if v in active and stamp == versions[v]:
                break
        else:
            raise AssertionError("VE priority queue exhausted early")
        ids = tuple(sorted(incidence[v]))
        touched = [factors[fid] for fid in ids]
        union = {v}
        for f in touched:
            union.update(f.scope)
        if len(union) != width:
            raise AssertionError("stale VE score was not invalidated")
        if width > max_factor_variables:
            return None
        maximum_width = max(maximum_width, width)
        context = tuple(sorted(union - {v}))
        work = (1 << len(context)) * 2 * max(1, len(touched))
        if work > max_operations - operations:
            return None
        operations += work
        values = []
        for packed in range(1 << len(context)):
            assignment = {u: bool(packed & (1 << i))
                          for i, u in enumerate(context)}
            summed = 0
            for value in (False, True):
                assignment[v] = value
                product = 1
                for f in touched:
                    key = sum(1 << i for i, u in enumerate(f.scope)
                              if assignment[u])
                    product *= f.table[key]
                    if product == 0:
                        break
                summed += product
            values.append(summed)

        affected = set()
        for fid in ids:
            f = factors.pop(fid)
            for u in f.scope:
                incidence[u].remove(fid)
                if u != v:
                    affected.add(u)

        if context:
            factors[next_id] = _IndexedFactor(context, tuple(values))
            for u in context:
                incidence[u].add(next_id)
                affected.add(u)
            next_id += 1
        else:
            constant *= values[0]

        active.remove(v)
        incidence.pop(v)
        for u in affected & active:
            versions[u] += 1
            push_score(u)

    if any(f.scope for f in factors.values()):
        raise AssertionError("non-constant factors survived VE")
    for f in factors.values():
        constant *= f.table[0]
    return VariableEliminationCount(
        constant, operations, maximum_width, len(component_variables))
