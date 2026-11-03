"""W-CRC-005: bounded exact hypergraph-defect Walsh response.

For a complete coherent signed rank-r CNF with d missing supports,
a flip set J of size >= r is satisfying iff EVERY r-subset of J is
missing. Such J is contained in the union U of missing supports.
Enumerating subsets of U is fixed-parameter in r*d (r <= 3); it does
not enumerate assignments of the full n-variable boundary.

This is familiar hypergraph-clique / lifted-counting mathematics, not
an algorithm for arbitrary CNF. All resource-limit failures return None.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from math import comb


@dataclass(frozen=True)
class DefectWalshResult:
    coefficients: dict[int, Fraction]
    rank: int
    missing_clauses: int
    defect_variables: int
    high_weight_flip_sets: int


def query_defect_walsh(
    normalized_violations: tuple[tuple[int, int], ...] | None,
    boundary_variables: tuple[int, ...],
    modes: tuple[int, ...],
    *,
    max_missing: int = 6,
    max_defect_variables: int = 18,
    max_subset_checks: int = 1 << 18,
) -> DefectWalshResult | None:
    """Return exact requested Walsh coefficients or None if unsupported.

    A normalized clause (zeros, ones) records the falsifying bits.
    The structural check scans the full C(n,r) support universe; the
    defect search scans at most 2^|U| subsets, with explicit caps.
    """
    if (not isinstance(max_missing, int) or max_missing < 0 or
        not isinstance(max_defect_variables, int) or max_defect_variables < 0 or
        not isinstance(max_subset_checks, int) or max_subset_checks < 1):
        raise ValueError("invalid defect enumeration limits")
    boundary_mask = 0
    for v in boundary_variables:
        if not isinstance(v, int) or v <= 0 or v > 256:
            raise ValueError("boundary IDs must be in 1..256")
        bit = 1 << (v - 1)
        if boundary_mask & bit:
            raise ValueError("duplicate boundary variable")
        boundary_mask |= bit
    if any(not isinstance(m, int) or m < 0 or (m & ~boundary_mask)
           for m in modes):
        raise ValueError("Walsh mode outside boundary")
    if normalized_violations is None or not normalized_violations:
        return None

    rank = (normalized_violations[0][0] |
            normalized_violations[0][1]).bit_count()
    if rank not in (2, 3):
        return None
    supports: set[int] = set()
    reference_ones = reference_zeros = active = 0
    for zeros, ones in normalized_violations:
        if zeros < 0 or ones < 0 or (zeros & ones) or (zeros | ones) & ~boundary_mask:
            raise ValueError("invalid normalized clause")
        scope = zeros | ones
        if scope.bit_count() != rank:
            return None
        # Clauses must use one globally coherent literal polarity.
        if (zeros & reference_zeros) or (ones & reference_ones):
            return None
        reference_ones |= zeros
        reference_zeros |= ones
        supports.add(scope)
        active |= scope

    variables = tuple(v for v in boundary_variables if active & (1 << (v - 1)))
    # The boundary tuple may be permuted; set membership, not order,
    # determines the canonical source support universe.
    n = len(variables)
    if n < rank or comb(n, rank) - len(supports) > max_missing:
        return None
    missing: set[int] = set()
    for chosen in combinations(sorted(variables), rank):
        mask = sum(1 << (v - 1) for v in chosen)
        if mask not in supports:
            missing.add(mask)
            if len(missing) > max_missing:
                return None

    defect_union = 0
    for support in missing:
        defect_union |= support
    defect_vars = tuple(v for v in sorted(variables)
                        if defect_union & (1 << (v - 1)))
    q = len(defect_vars)
    if q > max_defect_variables or (1 << q) > max_subset_checks:
        return None

    # Every admissible high-weight flip set is a clique in the
    # missing-support rank-r hypergraph, necessarily within U.
    high: list[int] = []
    for selection in range(1 << q):
        size = selection.bit_count()
        if size < rank or comb(size, rank) > len(missing):
            continue
        chosen = tuple(defect_vars[i] for i in range(q)
                       if selection & (1 << i))
        if all(sum(1 << (v - 1) for v in part) in missing
               for part in combinations(chosen, rank)):
            high.append(sum(1 << (v - 1) for v in chosen))

    free = boundary_mask ^ active
    coefficients: dict[int, Fraction] = {}
    for mode in modes:
        if mode & free:
            coefficients[mode] = Fraction()
            continue
        t = (mode & active).bit_count()
        weighted = 0
        for j in range(rank):
            for a in range(j + 1):
                if a <= t and j - a <= n - t:
                    weighted += (-1 if a & 1 else 1) * (
                        comb(t, a) * comb(n - t, j - a))
        weighted += sum(-1 if (mode & mask).bit_count() & 1 else 1
                        for mask in high)
        if (mode & reference_ones).bit_count() & 1:
            weighted = -weighted
        weighted <<= free.bit_count()
        coefficients[mode] = Fraction(weighted, 1 << len(boundary_variables))
    return DefectWalshResult(coefficients, rank, len(missing), q, len(high))
