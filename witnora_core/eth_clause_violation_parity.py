"""Finite experimental analogue of OpenAI's clause-violation parity tests.

For assignment x and source clause j, v_j(x) is 1 iff clause j is false.
Each row R enforces XOR_{j in R} v_j(x) = 0. Every source model
automatically passes, but arbitrary rows need NOT reject every nonmodel.

This deliberately enumerates all 2**n assignments to choose/check rows.
It is a controlled diagnostic, NOT an efficient general SAT algorithm,
and it does not implement the expander/interpolation/tensor results.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations
import json
from random import Random


CNF = tuple[tuple[int, ...], ...]


def _canonical(source: list[list[int]] | CNF, nvars: int) -> CNF:
    if nvars < 1 or nvars > 14:
        raise ValueError("finite experiment requires 1 <= nvars <= 14")
    result = tuple(tuple(int(lit) for lit in row) for row in source)
    if any(lit == 0 or abs(lit) > nvars for row in result for lit in row):
        raise ValueError("source literals must have variable IDs in 1..nvars")
    return result


def source_digest(source: CNF) -> str:
    raw = json.dumps(source, separators=(",", ":"), ensure_ascii=True)
    return sha256(raw.encode("ascii")).hexdigest()


def violation_mask(source: CNF, assignment_bits: int) -> int:
    """Bit j is 1 exactly when clause j is violated."""
    result = 0
    for j, clause in enumerate(source):
        if not any(bool(assignment_bits & (1 << (abs(lit) - 1))) == (lit > 0)
                   for lit in clause):
            result |= 1 << j
    return result


def parity_accepts(violations: int, rows: tuple[tuple[int, ...], ...]) -> bool:
    """Checks parity across clause *violation* bits, not variable XORs."""
    return all(sum(bool(violations & (1 << j)) for j in row) % 2 == 0
               for row in rows)


@dataclass(frozen=True)
class FiniteParitySketch:
    nvars: int
    clause_count: int
    digest: str
    rows: tuple[tuple[int, ...], ...]
    survivors: tuple[int, ...]
    satisfying_count: int


def build_finite_sketch(source: list[list[int]] | CNF, nvars: int,
                        *, seed: int = 73,
                        candidates_per_width: int = 100,
                        max_rows: int | None = None) -> FiniteParitySketch:
    """Greedily separate every *enumerated* realizable nonzero violation vector.

    Not a constructive subexponential reduction: selection and certification
    both use all 2**n assignments. For small diagnostic sources only.
    """
    cnf = _canonical(source, nvars)
    if candidates_per_width < 1:
        raise ValueError("need positive candidates_per_width")
    if max_rows is not None and max_rows < 0:
        raise ValueError("max_rows must be nonnegative")
    states = tuple(violation_mask(cnf, x) for x in range(1 << nvars))
    remaining = [state for state in states if state]
    count_models = len(states) - len(remaining)
    rng = Random(seed)
    candidate_set: set[tuple[int, ...]] = set()
    for width in range(2, min(5, len(cnf)) + 1):
        for _ in range(candidates_per_width):
            candidate_set.add(tuple(sorted(rng.sample(range(len(cnf)), width))))
    candidates = sorted(candidate_set, key=lambda row: (len(row), row))
    candidate_masks = [(row, sum(1 << j for j in row)) for row in candidates]

    rows: list[tuple[int, ...]] = []
    trace = [len(remaining)]
    while remaining:
        if max_rows is not None and len(rows) >= max_rows:
            raise ValueError("row budget exhausted before exact separation")
        best_row: tuple[int, ...] | None = None
        best_mask = 0
        best_rejected = 0
        for row, mask in candidate_masks:
            rejected = sum((state & mask).bit_count() & 1 for state in remaining)
            if rejected > best_rejected:
                best_row, best_mask, best_rejected = row, mask, rejected
        if best_row is None:
            # Guaranteed progress, but a singleton is just an original clause.
            first_violated_clause = (remaining[0] & -remaining[0]).bit_length() - 1
            best_row = (first_violated_clause,)
            best_mask = 1 << first_violated_clause
        rows.append(best_row)
        remaining = [state for state in remaining
                     if (state & best_mask).bit_count() % 2 == 0]
        trace.append(len(remaining))
    return FiniteParitySketch(
        nvars=nvars, clause_count=len(cnf), digest=source_digest(cnf),
        rows=tuple(rows), survivors=tuple(trace), satisfying_count=count_models,
    )


def verify_finite_sketch(source: list[list[int]] | CNF,
                         sketch: FiniteParitySketch) -> bool:
    """Exhaustively recheck source identity and BOTH directions of equivalence."""
    try:
        cnf = _canonical(source, sketch.nvars)
    except (ValueError, TypeError):
        return False
    if len(cnf) != sketch.clause_count or source_digest(cnf) != sketch.digest:
        return False
    for row in sketch.rows:
        if not row or tuple(sorted(set(row))) != row:
            return False
        if any(j < 0 or j >= len(cnf) for j in row):
            return False
    for x in range(1 << sketch.nvars):
        violations = violation_mask(cnf, x)
        if (violations == 0) != parity_accepts(violations, sketch.rows):
            return False
    return True


def is_complete_primal(source: list[list[int]] | CNF, nvars: int) -> bool:
    """Only a diagnostic for source family; not part of soundness."""
    edges = set()
    for clause in source:
        for x, y in combinations(clause, 2):
            edges.add(tuple(sorted((abs(x), abs(y)))))
    return len(edges) == nvars * (nvars - 1) // 2
