"""W-CRC-004: exact defect-bounded uniform-hypergraph Walsh oracle.

This is a special-case *lifted cardinality* identity, not a general
#SAT oracle or an asserted novel theorem. It recognizes a CNF formed
from every rank-r clause on n variables (r=2 or r=3) with globally
consistent literal polarities, optionally omitting at most r clauses.

Let b be the assignment making every chosen literal true. For each
assignment x let J be the set of variable bits flipped from b.
The CNF is satisfied exactly when:
  (1) |J| < r, or
  (2) |J| = r and its support is one of the missing clauses.
If |J| >= r+1, at least r+1 of its r-subsets are present as clauses.
Therefore the Walsh signed sum of the CNF for any mask T equals

 (-1)^parity(T & b) *
   (sum_{j=0}^{r-1} sum_{a=0}^j (-1)^a C(|T|,a) C(n-|T|,j-a)
    + sum_{H missing} (-1)^parity(T & H)).

Variables outside all clauses contribute either 2 if T omits them
or 0 otherwise. The final coefficient divides by 2^|boundary|.

Recognizing the complete/near-complete r-uniform signed hypergraph
takes O(m + C(n,r)) using direct support enumeration; coefficient
queries then take O(r^2 + d), where d<=r is the number of missing
supports. It never enumerates Boolean assignments.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from math import comb


@dataclass(frozen=True)
class OrbitWalshResult:
    coefficients: dict[int, Fraction]
    rank: int
    missing_clauses: int
    active_variables: int


def query_orbit_walsh(
    normalized_violations: tuple[tuple[int, int], ...] | None,
    boundary_variables: tuple[int, ...],
    modes: tuple[int, ...],
    *,
    max_missing: int = 3,
    backend: str = "python",
) -> OrbitWalshResult | None:
    """Exact Walsh coefficients on one near-complete signed r-hypergraph.

    Return None (unsupported) without guessing any coefficient.
    Each (zeros,ones) pair encodes a clause's falsifying assignment.
    """
    if not isinstance(max_missing, int) or max_missing < 0:
        raise ValueError("max_missing must be nonnegative")
    boundary_mask = 0
    for variable in boundary_variables:
        if not isinstance(variable, int) or variable <= 0 or variable > 256:
            raise ValueError("boundary IDs must be in 1..256")
        bit = 1 << (variable - 1)
        if boundary_mask & bit:
            raise ValueError("duplicate boundary ID")
        boundary_mask |= bit
    if any(not isinstance(mode, int) or mode < 0 or (mode & ~boundary_mask)
           for mode in modes):
        raise ValueError("mode outside boundary")
    if backend == "rust":
        from witnora_ve import crc_orbit_walsh_native
        data = crc_orbit_walsh_native(
            None if normalized_violations is None else
            [(str(z), str(o)) for z, o in normalized_violations],
            list(boundary_variables), [str(m) for m in modes], max_missing)
        if data is None:
            return None
        rows, rank, missing, active = data
        return OrbitWalshResult(
            {int(m): Fraction(int(n), int(d)) for m, n, d in rows},
            rank, missing, active)
    if backend != "python":
        raise ValueError("unknown orbit Walsh backend")
    if normalized_violations is None or not normalized_violations:
        return None

    supports: set[int] = set()
    reference_ones = 0
    reference_zeros = 0
    active = 0
    rank = (normalized_violations[0][0] |
            normalized_violations[0][1]).bit_count()
    if rank not in (2, 3):
        return None

    for zeros, ones in normalized_violations:
        if (zeros & ones) or (zeros | ones) & ~boundary_mask:
            raise ValueError("invalid normalized clause")
        scope = zeros | ones
        if scope.bit_count() != rank:
            return None
        # Every variable needs a fixed chosen literal across all clauses.
        if (zeros & reference_zeros) or (ones & reference_ones):
            return None
        reference_ones |= zeros
        reference_zeros |= ones
        active |= scope
        supports.add(scope)

    variables = tuple(
        i + 1 for i in range(256) if active & (1 << i)
    )
    n = len(variables)
    if n < rank:
        return None
    total = comb(n, rank)
    if total - len(supports) > min(rank, max_missing):
        return None
    # Exact completeness check; input size is already Theta(C(n,r))
    # for the supported family. No assignment-table construction.
    missing = []
    for subset in combinations(variables, rank):
        support = sum(1 << (v - 1) for v in subset)
        if support not in supports:
            missing.append(support)
    if len(missing) > min(rank, max_missing):
        return None

    free = boundary_mask ^ active
    coeffs: dict[int, Fraction] = {}
    for mode in modes:
        if mode & free:
            coeffs[mode] = Fraction()
            continue
        t = (mode & active).bit_count()
        weighted = 0
        for j in range(rank):
            for a in range(j + 1):
                if a <= t and j - a <= n - t:
                    weighted += (-1 if a & 1 else 1) * (
                        comb(t, a) * comb(n - t, j - a)
                    )
        weighted += sum(-1 if (mode & hole).bit_count() & 1 else 1
                        for hole in missing)
        if (mode & reference_ones).bit_count() & 1:
            weighted = -weighted
        weighted <<= free.bit_count()
        coeffs[mode] = Fraction(weighted, 1 << len(boundary_variables))
    return OrbitWalshResult(coeffs, rank, len(missing), n)
