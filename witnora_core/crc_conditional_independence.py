"""W-CRC-010: exact source-bound conditional structural independence.

Fixing separator variables can satisfy/delete clauses and disconnect
the residual source. With a verified full source model, disconnected
A/B residual primal components certify A ⟂ B *conditional on the
witness's separator assignment*, not unconditional independence.

A negative structural result means inconclusive, never dependence.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from witnora_core.crc_boundary import _mask, _normalized_clauses
from witnora_core.crc_structural_independence import (
    audit_structural_source_independence,
)


@dataclass(frozen=True)
class ConditionalStructuralAudit:
    separated_after_conditioning: bool
    separator_assignment: int
    separator_variables: tuple[int, ...]
    residual_components: int
    original_clauses: int
    residual_clauses: int


def audit_conditioned_source_independence(
    source_clauses: Iterable[Iterable[int]],
    boundary_variables: tuple[int, ...],
    left_group: tuple[int, ...],
    right_group: tuple[int, ...],
    separator: tuple[int, ...],
    satisfying_assignment: int,
    *, backend: str = "python",
) -> ConditionalStructuralAudit | None:
    """Sufficient exact certificate for A ⟂ B | (S = witness[S]).

    Return None if the offered assignment is not a source model.
    False is only an inconclusive graph test. Checking a given SAT
    model is cheap, but this function does not search for one.
    """
    boundary_mask = _mask(boundary_variables)
    if (not isinstance(satisfying_assignment, int) or
        satisfying_assignment < 0 or
        satisfying_assignment & ~boundary_mask):
        raise ValueError("invalid full boundary assignment mask")
    smask = _mask(separator)
    if smask & ~boundary_mask:
        raise ValueError("separator contains a non-boundary variable")
    if len(set(left_group)) != len(left_group) or not left_group:
        raise ValueError("invalid left group")
    if len(set(right_group)) != len(right_group) or not right_group:
        raise ValueError("invalid right group")
    if (set(left_group) & set(right_group) or
        set(left_group) & set(separator) or
        set(right_group) & set(separator)):
        raise ValueError("groups and separator must be disjoint")
    remaining = tuple(v for v in boundary_variables if v not in separator)
    # Validate group membership, even when all original clauses vanish.
    if any(v not in remaining for v in left_group + right_group):
        raise ValueError("group contains a non-boundary variable")

    if backend == "rust":
        from witnora_ve import crc_conditional_independence_native
        got = crc_conditional_independence_native(
            [list(row) for row in source_clauses], list(boundary_variables),
            list(left_group), list(right_group), list(separator),
            str(satisfying_assignment))
        if got is None:
            return None
        separated, condition_decimal, components, original_count, residual_count = got
        return ConditionalStructuralAudit(
            separated, int(condition_decimal), separator,
            components, original_count, residual_count)
    if backend != "python":
        raise ValueError("unknown conditional independence backend")

    normalized = _normalized_clauses(source_clauses, boundary_variables)
    if normalized is None:
        return None
    condition = satisfying_assignment & smask
    residual = []
    for zeros, ones in normalized:
        # A separator literal alone makes this clause true.
        if ((condition & zeros & smask) or
            ((~condition) & ones & smask)):
            continue
        z, o = zeros & ~smask, ones & ~smask
        if z | o == 0:
            return None  # separator alone falsified an original clause
        clause = []
        while z:
            bit = z & -z
            clause.append(bit.bit_length())
            z ^= bit
        while o:
            bit = o & -o
            clause.append(-bit.bit_length())
            o ^= bit
        residual.append(clause)

    sub = audit_structural_source_independence(
        residual, remaining, left_group, right_group,
        satisfying_assignment & ~smask)
    if sub is None:
        return None
    return ConditionalStructuralAudit(
        sub.separated, condition, separator,
        sub.source_components, len(normalized), len(residual),
    )
