"""W-CRC-001: exact asymmetric Fourier boundary contraction.

Research prototype only. The left side is an affine GF(2) system with
internal and boundary variables; the right side is a CNF on boundary
variables. This code never enumerates boundary assignments. It uses
exact rational arithmetic and hard limits on spectral and inclusion-
exclusion growth. It is not a general-purpose SAT algorithm.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable

from witnora_core.crc_shannon_oracle import query_walsh_coefficients
from witnora_core.crc_orbit_oracle import query_orbit_walsh
from witnora_core.crc_defect_oracle import query_defect_walsh
from witnora_core.crc_conflict_oracle import query_conflict_walsh


@dataclass(frozen=True)
class BoundaryCount:
    models: int
    left_fourier_terms: int
    right_violation_terms: int
    coefficient_queries: int
    internal_free_variables: int
    right_components: int
    coefficient_backend: str = "inclusion_exclusion"
    coefficient_states: int = 0
    coefficient_memo_hits: int = 0


def _mask(ids: Iterable[int]) -> int:
    result = 0
    for v in ids:
        if not isinstance(v, int) or v <= 0 or v > 256:
            raise ValueError("prototype variable IDs must be in 1..256; compactly relabel sparse IDs first")
        bit = 1 << (v - 1)
        if result & bit:
            raise ValueError("duplicate variable ID")
        result |= bit
    return result


def _project_affine(
    rows: Iterable[tuple[int, int]],
    internals: tuple[int, ...],
    boundary: tuple[int, ...],
) -> tuple[tuple[tuple[int, int], ...] | None, int]:
    """Project GF(2) rows through internal variables by exact elimination.

    For each boundary assignment, 2**free internal completions exist
    exactly when all returned boundary rows hold. None means no models.
    """
    i_mask, b_mask = _mask(internals), _mask(boundary)
    if i_mask & b_mask:
        raise ValueError("internal and boundary sets overlap")
    i_pivots: dict[int, tuple[int, int]] = {}
    residue: list[tuple[int, int]] = []
    for support, rhs in rows:
        if not isinstance(support, int) or support < 0 or rhs not in (0, 1):
            raise ValueError("invalid affine row")
        if support & ~(i_mask | b_mask):
            raise ValueError("row mentions an undeclared variable")
        m, b = support, rhs
        for v in sorted(internals):
            bit = 1 << (v - 1)
            if not (m & bit):
                continue
            if v in i_pivots:
                pm, pb = i_pivots[v]
                m ^= pm
                b ^= pb
            else:
                i_pivots[v] = (m, b)
                break
        else:
            residue.append((m, b))

    b_pivots: dict[int, tuple[int, int]] = {}
    for m, b in residue:
        for v in sorted(boundary):
            bit = 1 << (v - 1)
            if not (m & bit):
                continue
            if v in b_pivots:
                pm, pb = b_pivots[v]
                m ^= pm
                b ^= pb
            else:
                b_pivots[v] = (m, b)
                break
        else:
            if b:
                return None, len(internals) - len(i_pivots)
    return tuple(b_pivots[v] for v in sorted(b_pivots)), len(internals) - len(i_pivots)


def _sparse_fourier(
    rows: tuple[tuple[int, int], ...] | None,
    internal_free: int,
    *,
    max_terms: int,
) -> dict[int, Fraction] | None:
    if rows is None:
        return {}
    if max_terms <= 0:
        raise ValueError("max_terms must be positive")
    spectrum: dict[int, Fraction] = {0: Fraction(1 << internal_free)}
    for support, rhs in rows:
        next_spectrum: dict[int, Fraction] = {}
        sign = 1 if rhs == 0 else -1
        for mode, coef in spectrum.items():
            next_spectrum[mode] = next_spectrum.get(mode, Fraction()) + coef / 2
            shifted = mode ^ support
            next_spectrum[shifted] = next_spectrum.get(shifted, Fraction()) + sign * coef / 2
        spectrum = {mode: c for mode, c in next_spectrum.items() if c}
        if len(spectrum) > max_terms:
            return None
    return spectrum


def _normalized_clauses(
    clauses: Iterable[Iterable[int]],
    boundary: tuple[int, ...],
) -> tuple[tuple[int, int], ...] | None:
    """Return (must_be_zero, must_be_one) for each violated clause.

    A contradiction within a clause makes it tautological. An empty
    clause makes the CNF identically false (returns None).
    """
    allowed = _mask(boundary)
    results: set[tuple[int, int]] = set()
    for clause in clauses:
        zeros = ones = 0
        tautology = False
        for lit in clause:
            if not isinstance(lit, int) or lit == 0:
                raise ValueError("invalid signed literal")
            bit = 1 << (abs(lit) - 1)
            if not (allowed & bit):
                raise ValueError("right CNF mentions nonboundary variable")
            if lit > 0:
                if ones & bit:
                    tautology = True
                zeros |= bit
            else:
                if zeros & bit:
                    tautology = True
                ones |= bit
        if tautology:
            continue
        if not (zeros | ones):
            return None
        results.add((zeros, ones))
    return tuple(sorted(results))


def _right_violation_terms(
    clauses: tuple[tuple[int, int], ...] | None,
    *,
    max_subsets: int,
) -> tuple[tuple[int, int, Fraction], ...] | None:
    """Exact inclusion-exclusion terms for a CNF boundary function.

    Each term contributes coef * (-1)^<mode,ones> if every selected
    Walsh mode variable is fixed by zeros|ones.
    """
    if clauses is None:
        return ()
    if max_subsets < 1:
        raise ValueError("max_subsets must be positive")
    if (1 << len(clauses)) > max_subsets:
        return None
    terms: list[tuple[int, int, Fraction]] = []
    for selected in range(1 << len(clauses)):
        zeros = ones = 0
        valid = True
        for i, (z, o) in enumerate(clauses):
            if selected & (1 << i):
                zeros |= z
                ones |= o
                if zeros & ones:
                    valid = False
                    break
        if not valid:
            continue
        support = zeros | ones
        sign = -1 if selected.bit_count() & 1 else 1
        terms.append((support, ones, Fraction(sign, 1 << support.bit_count())))
    return tuple(terms)


def _coefficient(
    terms: tuple[tuple[int, int, Fraction], ...],
    mode: int,
) -> Fraction:
    total = Fraction()
    for support, ones, coef in terms:
        if mode & ~support:
            continue
        total += -coef if (mode & ones).bit_count() & 1 else coef
    return total



def _right_components(
    clauses: tuple[tuple[int, int], ...] | None,
    *,
    max_subsets: int,
) -> tuple[tuple[int, tuple[tuple[int, int, Fraction], ...]], ...] | None:
    """Factorize the CNF by disjoint clause-variable components.

    This is exact ordinary component decomposition in the coefficient
    oracle, not a new algorithmic theorem. Each component is expanded
    separately, with a shared inclusion-exclusion budget.
    """
    if clauses is None:
        return ((0, ()),)  # Empty clause: every Fourier coefficient is zero.
    if not clauses:
        return ()
    parent: dict[int, int] = {}

    def find(v: int) -> int:
        while parent[v] != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v

    for zeros, ones in clauses:
        scope = zeros | ones
        first = scope & -scope
        parent.setdefault(first, first)
        rest = scope ^ first
        while rest:
            bit = rest & -rest
            parent.setdefault(bit, bit)
            r1, r2 = find(first), find(bit)
            if r1 != r2:
                parent[r2] = r1
            rest ^= bit

    groups: dict[int, list[tuple[int, int]]] = {}
    scopes: dict[int, int] = {}
    for clause in clauses:
        scope = clause[0] | clause[1]
        root = find(scope & -scope)
        groups.setdefault(root, []).append(clause)
        scopes[root] = scopes.get(root, 0) | scope

    remaining = max_subsets
    components = []
    for root in sorted(groups):
        subset_count = 1 << len(groups[root])
        if subset_count > remaining:
            return None
        terms = _right_violation_terms(tuple(groups[root]), max_subsets=remaining)
        if terms is None:
            return None
        remaining -= subset_count
        components.append((scopes[root], terms))
    return tuple(components)


def _component_coefficient(
    components: tuple[tuple[int, tuple[tuple[int, int, Fraction], ...]], ...],
    mode: int,
) -> Fraction:
    union = 0
    for scope, _ in components:
        union |= scope
    if mode & ~union:
        return Fraction()
    result = Fraction(1)
    for scope, terms in components:
        result *= _coefficient(terms, mode & scope)
        if result == 0:
            return result
    return result

def count_asymmetric_boundary(
    left_affine_rows: Iterable[tuple[int, int]],
    internal_variables: Iterable[int],
    boundary_variables: Iterable[int],
    right_clauses: Iterable[Iterable[int]],
    *,
    max_spectrum_terms: int = 4096,
    max_inclusion_subsets: int = 4096,
    max_coefficient_states: int | None = None,
    enable_orbit_oracle: bool = False,
    enable_defect_oracle: bool = False,
    enable_conflict_oracle: bool = False,
    coefficient_backend: str = "python",
    max_rust_coefficient_operations: int = 2000000,
) -> BoundaryCount | None:
    """Count an affine left region and boundary-only CNF right region.

    Returns None on budget exhaustion, never an incorrect model count.
    """
    if coefficient_backend not in ("python", "rust_inclusion_exclusion"):
        raise ValueError("unknown exact coefficient backend")
    if (not isinstance(max_rust_coefficient_operations, int)
            or max_rust_coefficient_operations < 1):
        raise ValueError("invalid native coefficient operation budget")
    internals = tuple(internal_variables)
    boundary = tuple(boundary_variables)
    rows, free = _project_affine(tuple(left_affine_rows), internals, boundary)
    spectrum = _sparse_fourier(rows, free, max_terms=max_spectrum_terms)
    if spectrum is None:
        return None
    clauses = _normalized_clauses(right_clauses, boundary)
    native = None
    if coefficient_backend == "rust_inclusion_exclusion":
        from witnora_core.crc_rust_walsh import query_right_walsh_in_rust
        native = query_right_walsh_in_rust(
            clauses, boundary, tuple(spectrum),
            max_subsets=max_inclusion_subsets,
            max_operations=max_rust_coefficient_operations,
        )
        if native is None:
            # Explicit Rust inclusion-exclusion caps fail closed; do not
            # silently switch to Python's other coefficient algorithms.
            return None
        components = ()
    else:
        components = _right_components(clauses, max_subsets=max_inclusion_subsets)
    if components is None:
        # Optional exact, recognizable dense nonlinear family. It
        # computes only requested Walsh modes using cardinality
        # identities; it never estimates an unsupported coefficient.
        orbit = (query_orbit_walsh(clauses, boundary, tuple(spectrum))
                 if enable_orbit_oracle else None)
        # A separate opt-in FPT-by-defects enumeration also admits
        # tetrahedral/high-order missing-support patterns. The
        # low-defect cardinality path retains priority when available.
        defect = (query_defect_walsh(clauses, boundary, tuple(spectrum))
                  if orbit is None and enable_defect_oracle else None)
        conflict = (query_conflict_walsh(clauses, boundary, tuple(spectrum))
                    if orbit is None and defect is None and
                    enable_conflict_oracle else None)
        exact = (orbit if orbit is not None else
                 defect if defect is not None else conflict)
        if exact is not None:
            accumulated = sum(
                (coef * exact.coefficients[mode]
                 for mode, coef in spectrum.items()), Fraction(),
            )
            backend = ("orbit_cardinality" if orbit is not None else
                       "defect_hypergraph" if defect is not None else
                       "conflict_walsh")
            right_terms = right_components = states = hits = 0
        else:
            # Exact bounded Shannon fallback for general overlap.
            if max_coefficient_states is None:
                return None
            query = query_walsh_coefficients(
                clauses, boundary, tuple(spectrum),
                max_states=max_coefficient_states,
            )
            if query is None:
                return None
            accumulated = sum(
                (coef * query.coefficients[mode]
                 for mode, coef in spectrum.items()), Fraction(),
            )
            backend = "shannon"
            right_terms = right_components = 0
            states = query.states
            hits = query.memo_hits
    else:
        if native is not None:
            accumulated = sum(
                (coef * native.coefficients[mode]
                 for mode, coef in spectrum.items()), Fraction(),
            )
            backend = "inclusion_exclusion_rust"
            right_terms = native.compatible_terms
            right_components = native.components
        else:
            accumulated = sum(
                (coef * _component_coefficient(components, mode)
                 for mode, coef in spectrum.items()), Fraction(),
            )
            backend = "inclusion_exclusion"
            right_terms = sum(len(terms) for _, terms in components)
            right_components = len(components)
        states = hits = 0
    result = (1 << len(boundary)) * accumulated
    if result.denominator != 1 or result < 0:
        raise AssertionError("exact counting invariant violated")
    return BoundaryCount(
        result.numerator, len(spectrum), right_terms, len(spectrum), free,
        right_components, backend, states, hits,
    )
