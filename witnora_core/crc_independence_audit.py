"""W-CRC-008: exact source-derived Fourier independence audit.

For the model indicator f of one supported coherent near-complete
uniform source, groups A and B are independent under the uniform
distribution over f-models iff for every S subseteq A and T subseteq B

    hat(f)(S union T) * hat(f)(empty) == hat(f)(S) * hat(f)(T).

This checks *all* joint Fourier moments, not only pairwise variable
correlations. It is an exact small-group audit, not a cheap universal
separator or an independent SAT solving algorithm.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable

from witnora_core.crc_boundary import _normalized_clauses
from witnora_core.crc_defect_oracle import query_defect_walsh


@dataclass(frozen=True)
class IndependenceAudit:
    independent: bool
    checked_modes: int
    witness_left: int | None
    witness_right: int | None
    discrepancy: Fraction


def _all_submasks(bits: tuple[int, ...]) -> tuple[int, ...]:
    masks = [0]
    for bit in bits:
        masks += [mask | bit for mask in tuple(masks)]
    return tuple(masks)


def audit_defect_source_independence(
    source_clauses: Iterable[Iterable[int]],
    boundary_variables: tuple[int, ...],
    left_group: tuple[int, ...],
    right_group: tuple[int, ...],
    *,
    max_modes: int = 4096,
    max_missing: int = 6,
) -> IndependenceAudit | None:
    """Verify exact independence or return a cross-moment witness.

    None means the base family or the resource bound was unsupported,
    not that group independence was false.
    """
    if not isinstance(max_modes, int) or max_modes < 1:
        raise ValueError("invalid Fourier mode cap")
    bset = set(boundary_variables)
    for group in (left_group, right_group):
        if not group or len(set(group)) != len(group):
            raise ValueError("each group must be nonempty and duplicate-free")
        if any(v not in bset for v in group):
            raise ValueError("group contains non-boundary variable")
    if set(left_group) & set(right_group):
        raise ValueError("groups overlap")
    left_bits = tuple(1 << (v - 1) for v in left_group)
    right_bits = tuple(1 << (v - 1) for v in right_group)
    if len(left_bits) + len(right_bits) > 20:
        return None
    needed_count = 1 << (len(left_bits) + len(right_bits))
    if needed_count > max_modes:
        return None

    normalized = _normalized_clauses(source_clauses, boundary_variables)
    if normalized is None:
        return None
    left_masks = _all_submasks(left_bits)
    right_masks = _all_submasks(right_bits)
    modes = tuple(sorted(l | r for l in left_masks for r in right_masks))
    base = query_defect_walsh(
        normalized, boundary_variables, modes, max_missing=max_missing)
    if base is None:
        return None
    coefficients = base.coefficients
    c0 = coefficients[0]
    if c0 <= 0:
        return None

    for l in left_masks:
        for r in right_masks:
            delta = coefficients[l | r] * c0 - coefficients[l] * coefficients[r]
            if delta:
                return IndependenceAudit(
                    False, len(modes), l, r, delta)
    return IndependenceAudit(True, len(modes), None, None, Fraction())
