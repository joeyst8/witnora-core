"""W-CRC-012: exact #SAT by bounded source min-cut conditioning.

Discover a small primal separator under a checked full SAT witness,
enumerate all separator assignments, and count each residual primal
component by exhaustive local enumeration. Multiply component counts
and sum the branches. Every resource bound fails closed with None.

This is standard cutset conditioning / component decomposition. It is
not a polynomial-time general #SAT algorithm.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from witnora_core.crc_boundary import _normalized_clauses
from witnora_core.crc_separator_discovery import discover_source_separator
from witnora_core.crc_variable_elimination import count_component_by_elimination


@dataclass(frozen=True)
class CutsetModelCount:
    models: int
    separator: tuple[int, ...]
    separator_branches: int
    max_residual_component: int
    assignment_states: int
    max_residual_components: int
    primal_edges: int
    component_backend: str = "enumeration"
    ve_operations: int = 0
    ve_max_factor_variables: int = 0


def count_source_by_separator(
    source_clauses: Iterable[Iterable[int]],
    boundary_variables: tuple[int, ...],
    left_group: tuple[int, ...],
    right_group: tuple[int, ...],
    satisfying_assignment: int,
    *,
    max_separator_size: int = 4,
    max_primal_edges: int = 10000,
    max_component_variables: int = 14,
    max_assignment_states: int = 1000000,
    max_separator_branches: int = 64,
    component_backend: str = "enumeration",
    max_ve_factor_variables: int = 6,
    max_ve_operations: int = 1000000,
) -> CutsetModelCount | None:
    """Exact source #SAT with strict cut, component and state caps.

    The admitted separator is minimum only in the *original* primal
    graph, and a supplied full source witness must be independently
    valid. This counts all assignments, not merely the witness's
    chosen separator branch.
    """
    if (not isinstance(max_component_variables, int) or
        max_component_variables < 1 or
        not isinstance(max_assignment_states, int) or
        max_assignment_states < 1 or
        not isinstance(max_separator_branches, int) or
        not 1 <= max_separator_branches <= 256):
        raise ValueError("invalid component/state cap")
    if component_backend not in ("enumeration", "variable_elimination"):
        raise ValueError("unknown exact component backend")
    if (not isinstance(max_ve_factor_variables, int) or
        not 1 <= max_ve_factor_variables <= 16 or
        not isinstance(max_ve_operations, int) or max_ve_operations < 1):
        raise ValueError("invalid VE width or operation budget")
    source = tuple(tuple(c) for c in source_clauses)
    cut = discover_source_separator(
        source, boundary_variables, left_group, right_group,
        satisfying_assignment, max_separator_size=max_separator_size,
        max_primal_edges=max_primal_edges)
    if cut is None:
        return None
    normalized = _normalized_clauses(source, boundary_variables)
    if normalized is None:
        raise AssertionError("checked source became unsatisfiable")
    separator = cut.separator
    if (1 << len(separator)) > max_separator_branches:
        return None
    separator_mask = sum(1 << (v - 1) for v in separator)
    remaining = tuple(v for v in boundary_variables
                      if v not in set(separator))
    total, states, biggest, largest_comp_count = 0, 0, 0, 0
    ve_ops, ve_width = 0, 0
    for branch in range(1 << len(separator)):
        condition = sum(1 << (v - 1) for i, v in enumerate(separator)
                        if branch & (1 << i))
        residual = []
        incompatible = False
        for zeros, ones in normalized:
            if ((condition & zeros & separator_mask) or
                ((~condition) & ones & separator_mask)):
                continue
            z, o = zeros & ~separator_mask, ones & ~separator_mask
            if not (z | o):
                incompatible = True
                break
            residual.append((z, o))
        if incompatible:
            continue

        parent = {v: v for v in remaining}
        def root(v):
            while parent[v] != v:
                parent[v] = parent[parent[v]]
                v = parent[v]
            return v
        def union(a, b):
            a, b = root(a), root(b)
            if a != b:
                parent[b] = a

        for zeros, ones in residual:
            scope = zeros | ones
            first = (scope & -scope).bit_length()
            rest = scope ^ (1 << (first - 1))
            while rest:
                bit = rest & -rest
                union(first, bit.bit_length())
                rest ^= bit

        variables_by_component = {}
        for v in remaining:
            variables_by_component.setdefault(root(v), []).append(v)
        clauses_by_component = {}
        for z, o in residual:
            first = (z | o) & -(z | o)
            clauses_by_component.setdefault(
                root(first.bit_length()), []).append((z, o))

        largest_comp_count = max(largest_comp_count,
                                 len(variables_by_component))
        branch_models = 1
        for comp, variables in variables_by_component.items():
            local_clauses = clauses_by_component.get(comp, ())
            if not local_clauses:
                branch_models <<= len(variables)
                continue
            width = len(variables)
            biggest = max(biggest, width)
            if component_backend == "variable_elimination":
                remaining_ve_budget = max_ve_operations - ve_ops
                if remaining_ve_budget < 1:
                    return None
                ve = count_component_by_elimination(
                    local_clauses, tuple(variables),
                    max_factor_variables=max_ve_factor_variables,
                    max_operations=remaining_ve_budget)
                if ve is None:
                    return None
                ve_ops += ve.operations
                ve_width = max(ve_width, ve.max_factor_variables)
                branch_models *= ve.models
                if branch_models == 0:
                    break
                continue
            if width > max_component_variables:
                return None
            attempts = 1 << width
            if attempts > max_assignment_states - states:
                return None
            states += attempts
            local_count = 0
            for packed in range(attempts):
                bits = 0
                for i, var in enumerate(variables):
                    if packed & (1 << i):
                        bits |= 1 << (var - 1)
                if all(not ((bits & z) == 0 and (bits & o) == o)
                       for z, o in local_clauses):
                    local_count += 1
            branch_models *= local_count
            if branch_models == 0:
                break
        total += branch_models
    return CutsetModelCount(
        total, separator, 1 << len(separator), biggest, states,
        largest_comp_count, cut.primal_edges,
        component_backend, ve_ops, ve_width)
