"""Non-enumerative dense parity baseline and finite constraint geometry audits.

For a fixed n-variable CNF, drawing r=n+s independently uniform rows over
its m clause-violation bits gives
    Pr[some nonmodel survives all rows] <= 2**(n-r) = 2**(-s).
Each nonzero violation vector passes one uniform row with probability 1/2;
a union bound covers <=2**n nonsatisfying assignments.

This probability statement is about *ideal independent random bits* and a
source fixed before the draw. Seeded Random is a reproducible experiment, NOT
a rigorous randomness certificate. The rows are DENSE (expected width m/2);
this is not OpenAI's sparse construction, a proof of exactness for any seed,
or a fast SAT/counting algorithm. The builder never enumerates assignments.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from random import Random, SystemRandom

from witnora_core.eth_clause_violation_parity import (
    CNF, parity_accepts, source_digest, violation_mask,
)


def canonical_source(source: list[list[int]] | CNF, nvars: int) -> CNF:
    """Validate IDs independently of the <=14-variable finite-audit cap."""
    if nvars < 1:
        raise ValueError("nvars must be positive")
    result = tuple(tuple(int(lit) for lit in row) for row in source)
    if any(lit == 0 or abs(lit) > nvars for row in result for lit in row):
        raise ValueError("source literal IDs must be in 1..nvars")
    return result


@dataclass(frozen=True)
class DenseParitySketch:
    nvars: int
    clause_count: int
    digest: str
    security_bits: int
    rows: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class CollisionProfile:
    assignments: int
    source_models: int
    nonmodels: int
    false_positives: int
    singleton_violation_clause_ids: frozenset[int]


def build_dense_random_sketch(
    source: list[list[int]] | CNF, nvars: int, *,
    security_bits: int = 20, seed: int | None = None, backend: str = "python",
) -> DenseParitySketch:
    """Construct r=n+security_bits rows in O(r*m), with NO SAT enumeration.

    seed=None uses SystemRandom; a fixed seed permits frozen diagnostics.
    In either case a concrete sketch is NOT automatically certified exact.
    """
    cnf = canonical_source(source, nvars)
    if security_bits < 0:
        raise ValueError("security_bits must be nonnegative")
    rng = SystemRandom() if seed is None else Random(seed)
    m = len(cnf)
    if backend == "rust":
        from witnora_ve import dense_geometry_rows_native
        bitmaps = [str(rng.getrandbits(m)) for _ in range(nvars + security_bits)]
        rows = [tuple(row) for row in dense_geometry_rows_native(bitmaps, m)]
    elif backend == "python":
        rows = []
        for _ in range(nvars + security_bits):
            bitmap = rng.getrandbits(m)
            rows.append(tuple(j for j in range(m) if (bitmap >> j) & 1))
    else:
        raise ValueError("unknown dense geometry backend")
    return DenseParitySketch(
        nvars=nvars, clause_count=m, digest=source_digest(cnf),
        security_bits=security_bits, rows=tuple(rows),
    )


def validate_dense_sketch(
    source: list[list[int]] | CNF, sketch: DenseParitySketch,
    *, backend: str = "python",
) -> CNF:
    """Bind the source to each row, but do NOT purport to prove exactness."""
    cnf = canonical_source(source, sketch.nvars)
    if backend == "rust":
        from witnora_ve import dense_geometry_validate_native
        if sketch.security_bits < 0:
            raise ValueError("incorrect row count")
        dense_geometry_validate_native(
            [list(row) for row in cnf], sketch.nvars, sketch.clause_count,
            sketch.digest, sketch.security_bits, [list(row) for row in sketch.rows])
        return cnf
    if backend != "python":
        raise ValueError("unknown dense geometry backend")
    if len(cnf) != sketch.clause_count or source_digest(cnf) != sketch.digest:
        raise ValueError("source identity mismatch")
    if sketch.security_bits < 0 or len(sketch.rows) != sketch.nvars + sketch.security_bits:
        raise ValueError("incorrect row count")
    for row in sketch.rows:
        if tuple(sorted(set(row))) != row:
            raise ValueError("noncanonical row IDs")
        if any(j < 0 or j >= len(cnf) for j in row):
            raise ValueError("row references absent clause")
    return cnf


def audit_small_collisions(
    source: list[list[int]] | CNF, sketch: DenseParitySketch,
    *, max_variables: int = 14, backend: str = "python",
) -> CollisionProfile:
    """EXPONENTIAL small-case audit, separate from the nonenumerative builder."""
    cnf = validate_dense_sketch(source, sketch, backend=backend)
    if sketch.nvars > max_variables:
        raise ValueError("exhaustive audit restricted to small experiments")
    if backend == "rust":
        from witnora_ve import dense_geometry_audit_native
        total, models, nonmodels, fp, singleton = dense_geometry_audit_native(
            [list(row) for row in cnf], sketch.nvars,
            [list(row) for row in sketch.rows], max_variables)
        return CollisionProfile(total, models, nonmodels, fp, frozenset(singleton))
    source_models = false_positives = 0
    singleton_ids: set[int] = set()
    for bits in range(1 << sketch.nvars):
        violations = violation_mask(cnf, bits)
        if violations == 0:
            source_models += 1
        else:
            if violations.bit_count() == 1:
                singleton_ids.add(violations.bit_length() - 1)
            if parity_accepts(violations, sketch.rows):
                false_positives += 1
    total = 1 << sketch.nvars
    return CollisionProfile(
        assignments=total,
        source_models=source_models,
        nonmodels=total - source_models,
        false_positives=false_positives,
        singleton_violation_clause_ids=frozenset(singleton_ids),
    )


def singleton_coverage_lower_bound(singleton_ids: frozenset[int],
                                   max_row_width: int, *, backend: str = "python") -> int:
    """A necessary row-count bound when these unit vectors are realizable.

    Every clause j with realizable violation vector e_j must occur in at
    least one selected row. Thus r*max_row_width >= len(singleton_ids).
    This bound does NOT assert anything about SAT decision complexity.
    """
    if max_row_width < 1:
        raise ValueError("max_row_width must be positive")
    if backend == "rust":
        from witnora_ve import dense_geometry_singleton_bound_native
        return dense_geometry_singleton_bound_native(len(singleton_ids), max_row_width)
    if backend != "python":
        raise ValueError("unknown dense geometry backend")
    return ceil(len(singleton_ids) / max_row_width)


def row_statistics(sketch: DenseParitySketch, *, backend: str = "python") -> tuple[int, float, int]:
    if backend == "rust":
        from witnora_ve import dense_geometry_row_stats_native
        return dense_geometry_row_stats_native([list(row) for row in sketch.rows])
    if backend != "python":
        raise ValueError("unknown dense geometry backend")
    sizes = [len(row) for row in sketch.rows]
    if not sizes:
        return (0, 0.0, 0)
    return (min(sizes), sum(sizes) / len(sizes), max(sizes))
