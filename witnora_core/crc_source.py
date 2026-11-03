"""W-CRC-001 source-CNF adapter for exact small XOR gadgets.

This parser/extractor accepts arbitrary signed CNF clauses, but the
bounded coefficient engine may return None. Only *complete* canonical
k-XOR clause blocks (k=1,2,3) are moved into affine equations; all
other clauses remain in the exact right-hand CNF. This avoids treating
arbitrary parity sketches as equivalent to their source CNF.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable

from witnora_core.crc_boundary import BoundaryCount, count_asymmetric_boundary


@dataclass(frozen=True)
class SourceCRCResult:
    models: int
    extracted_affine_rows: int
    residual_clauses: int
    boundary_variables: int
    internal_variables: int
    coefficient_stats: BoundaryCount


def _canonical_signed_clause(clause: Iterable[int], nvars: int) -> tuple[int, ...] | None:
    literals: set[int] = set()
    tautology = False
    for lit in clause:
        if not isinstance(lit, int) or lit == 0 or abs(lit) > nvars:
            raise ValueError("source literal out of range")
        if -lit in literals:
            tautology = True
        literals.add(lit)
    return None if tautology else tuple(sorted(literals, key=lambda lit: (abs(lit), lit)))


def _xor_cnf(variables: tuple[int, ...], rhs: int) -> frozenset[tuple[int, ...]]:
    """The complete set of clauses forbidding wrong-parity assignments.

    Every clause is falsified by exactly one assignment to the k
    variables, so the resulting conjunction is iff their XOR is rhs.
    """
    clauses = []
    for values in product((0, 1), repeat=len(variables)):
        if sum(values) % 2 == rhs:
            continue
        clauses.append(tuple(v if value == 0 else -v
                             for v, value in zip(variables, values)))
    return frozenset(clauses)


def extract_exact_small_xors(
    raw_clauses: Iterable[Iterable[int]],
    nvars: int,
) -> tuple[tuple[tuple[int, int], ...], tuple[tuple[int, ...], ...]]:
    """Return exact affine equations and all remaining source clauses.

    k-XOR recognition requires every forbidden-pattern clause for a
    particular variable support, with k <= 3. No partial extraction.
    """
    if not isinstance(nvars, int) or nvars < 0 or nvars > 256:
        raise ValueError("W-CRC prototype supports nvars in 0..256")
    source = set()
    for clause in raw_clauses:
        canonical = _canonical_signed_clause(clause, nvars)
        if canonical is not None:
            source.add(canonical)
    groups: dict[tuple[int, ...], set[tuple[int, ...]]] = {}
    for clause in source:
        if 1 <= len(clause) <= 3:
            support = tuple(sorted(abs(lit) for lit in clause))
            groups.setdefault(support, set()).add(clause)
    rows: list[tuple[int, int]] = []
    for variables in sorted(groups):
        for rhs in (0, 1):
            expected = _xor_cnf(variables, rhs)
            if expected.issubset(source):
                rows.append((sum(1 << (v - 1) for v in variables), rhs))
                source.difference_update(expected)
    return tuple(rows), tuple(sorted(source, key=lambda c: (len(c), c)))


def count_signed_cnf_crc(
    raw_clauses: Iterable[Iterable[int]],
    nvars: int,
    *,
    max_spectrum_terms: int = 4096,
    max_inclusion_subsets: int = 4096,
    max_coefficient_states: int | None = None,
    enable_orbit_oracle: bool = False,
    enable_defect_oracle: bool = False,
    enable_conflict_oracle: bool = False,
    source_preprocessor: str = "none",
    source_extractor: str = "python",
    max_preprocess_passes: int = 64,
    max_preprocess_clause_visits: int = 1000000,
) -> SourceCRCResult | None:
    """Exact count or None on a declared resource budget.

    All unrecognized CNF clauses stay in the right CNF; its variables
    define the boundary. Everything else is an internal affine/free
    variable. No source-clause information is discarded.
    """
    if source_preprocessor not in ("none", "rust_consensus", "rust_adaptive"):
        raise ValueError("unknown exact source preprocessor")
    if source_preprocessor in ("rust_consensus", "rust_adaptive"):
        from witnora_core.crc_rust_preprocess import simplify_source_in_rust
        simplified = simplify_source_in_rust(
            raw_clauses, nvars, max_passes=max_preprocess_passes,
            max_clause_visits=max_preprocess_clause_visits,
            adaptive=(source_preprocessor == "rust_adaptive"))
        if simplified is None:
            return None
        raw_clauses = simplified.clauses
    if source_extractor == "python":
        rows, residual = extract_exact_small_xors(raw_clauses, nvars)
    elif source_extractor == "rust":
        from witnora_core.crc_rust_xor import extract_small_xors_in_rust
        rows, residual = extract_small_xors_in_rust(raw_clauses, nvars)
    else:
        raise ValueError("unknown exact source extractor")
    boundary = tuple(sorted({abs(lit) for clause in residual for lit in clause}))
    bset = set(boundary)
    internal = tuple(v for v in range(1, nvars + 1) if v not in bset)
    result = count_asymmetric_boundary(
        rows, internal, boundary, residual,
        max_spectrum_terms=max_spectrum_terms,
        max_inclusion_subsets=max_inclusion_subsets,
        max_coefficient_states=max_coefficient_states,
        enable_orbit_oracle=enable_orbit_oracle,
        enable_defect_oracle=enable_defect_oracle,
        enable_conflict_oracle=enable_conflict_oracle,
    )
    if result is None:
        return None
    return SourceCRCResult(
        result.models, len(rows), len(residual),
        len(boundary), len(internal), result,
    )
