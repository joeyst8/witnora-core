"""W-CRC-006: exact bounded mixed-polarity Walsh correction.

Separate a nearly complete coherent uniform CNF F0 from a bounded
number of exceptional sign clauses E on variable set A. Fourier
convolution gives coefficient(F0 * E, T) =
    sum_{U subseteq A} coefficient(E,U) * coefficient(F0,T xor U).
The exception transform is computed by a small exact FWHT on A.
The base coefficients come from the checked bounded defect-hypergraph
oracle. Unsupported or over-budget instances return None.

This is established Walsh convolution/lifted counting, not an
arbitrary-CNF polynomial algorithm.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from witnora_core.crc_defect_oracle import query_defect_walsh


@dataclass(frozen=True)
class ConflictWalshResult:
    coefficients: dict[int, Fraction]
    exceptions: int
    exception_variables: int
    base_missing_clauses: int
    base_query_modes: int


def query_conflict_walsh(
    normalized_violations: tuple[tuple[int, int], ...] | None,
    boundary_variables: tuple[int, ...],
    modes: tuple[int, ...],
    *,
    max_exception_clauses: int = 2,
    max_exception_variables: int = 6,
    max_base_mode_queries: int = 4096,
    max_missing: int = 6,
) -> ConflictWalshResult | None:
    """Exact normalized Walsh response to a few conflicting-sign clauses."""
    if (not isinstance(max_exception_clauses, int) or max_exception_clauses < 0 or
        not isinstance(max_exception_variables, int) or max_exception_variables < 0 or
        not isinstance(max_base_mode_queries, int) or max_base_mode_queries < 1 or
        not isinstance(max_missing, int) or max_missing < 0):
        raise ValueError("invalid mixed-polarity resource limit")
    boundary_mask = 0
    for v in boundary_variables:
        if not isinstance(v, int) or v < 1 or v > 256:
            raise ValueError("boundary IDs must be in 1..256")
        bit = 1 << (v - 1)
        if boundary_mask & bit:
            raise ValueError("duplicate boundary variable")
        boundary_mask |= bit
    if any(not isinstance(m, int) or m < 0 or (m & ~boundary_mask)
           for m in modes):
        raise ValueError("Walsh mode outside boundary")
    if not normalized_violations:
        return None
    rank = (normalized_violations[0][0] |
            normalized_violations[0][1]).bit_count()
    if rank not in (2, 3):
        return None

    positive_count: dict[int, int] = {}
    negative_count: dict[int, int] = {}
    for zeros, ones in normalized_violations:
        if (zeros < 0 or ones < 0 or (zeros & ones) or
            ((zeros | ones) & ~boundary_mask)):
            raise ValueError("invalid normalized clause")
        if (zeros | ones).bit_count() != rank:
            return None
        rest = zeros
        while rest:
            bit = rest & -rest
            positive_count[bit] = positive_count.get(bit, 0) + 1
            rest ^= bit
        rest = ones
        while rest:
            bit = rest & -rest
            negative_count[bit] = negative_count.get(bit, 0) + 1
            rest ^= bit

    reference_positive = reference_negative = 0
    for bit in positive_count.keys() | negative_count.keys():
        pos = positive_count.get(bit, 0)
        neg = negative_count.get(bit, 0)
        if pos == neg:
            return None  # no unique coherent reference polarity
        if pos > neg:
            reference_positive |= bit
        else:
            reference_negative |= bit

    base: list[tuple[int, int]] = []
    exceptions: list[tuple[int, int]] = []
    exception_mask = 0
    for zeros, ones in normalized_violations:
        if (zeros & reference_negative) or (ones & reference_positive):
            exceptions.append((zeros, ones))
            exception_mask |= zeros | ones
        else:
            base.append((zeros, ones))
    if not exceptions or len(exceptions) > max_exception_clauses:
        return None
    exception_bits = tuple(
        1 << (v - 1) for v in boundary_variables
        if exception_mask & (1 << (v - 1)))
    q = len(exception_bits)
    if q > max_exception_variables or (1 << q) > max_base_mode_queries:
        return None

    # Evaluate the exceptional CNF on its own variable set.
    # The corresponding 2^q Walsh transform is an *exact* small
    # integer transform; no full-boundary assignment is enumerated.
    local_masks = []
    values = []
    for subset in range(1 << q):
        assignment = sum(bit for i, bit in enumerate(exception_bits)
                         if subset & (1 << i))
        local_masks.append(assignment)
        satisfied = all(not ((assignment & z) == 0 and
                             (assignment & o) == o)
                        for z, o in exceptions)
        values.append(int(satisfied))

    # In-place fast Walsh-Hadamard transform of the 0/1 truth table.
    for i in range(q):
        stride = 1 << i
        for base_index in range(0, 1 << q, stride << 1):
            for offset in range(stride):
                left = base_index + offset
                right = left + stride
                a, b = values[left], values[right]
                values[left], values[right] = a + b, a - b

    active_modes = tuple(i for i, c in enumerate(values) if c)
    needed = set()
    for mode in modes:
        for i in active_modes:
            needed.add(mode ^ local_masks[i])
            if len(needed) > max_base_mode_queries:
                return None

    base_result = query_defect_walsh(
        tuple(base), boundary_variables, tuple(sorted(needed)),
        max_missing=max_missing,
    )
    if base_result is None:
        return None
    denominator = 1 << q
    coefficients = {
        mode: sum(
            (Fraction(values[i], denominator) *
             base_result.coefficients[mode ^ local_masks[i]]
             for i in active_modes), Fraction(),
        )
        for mode in modes
    }
    return ConflictWalshResult(
        coefficients, len(exceptions), q,
        base_result.missing_clauses, len(needed),
    )
