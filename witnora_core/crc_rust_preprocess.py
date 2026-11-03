"""Native Rust source-preserving CNF simplification (opt-in).

The Rust module applies exact Boolean consensus and unit propagation.
Each transformation preserves every satisfying assignment over the
declared variables; it is not a new #SAT shortcut or Lean proof.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class RustSourceSimplification:
    clauses: tuple[tuple[int, ...], ...]
    passes: int
    consensus_pairs: int
    original_clauses: int


def simplify_source_in_rust(
    raw_clauses: Iterable[Iterable[int]], nvars: int, *,
    max_passes: int = 64, max_clause_visits: int = 1000000,
) -> RustSourceSimplification | None:
    """Return logically equivalent source CNF, or None on exact budget cap."""
    if (not isinstance(nvars, int) or not 0 <= nvars <= 256
            or not isinstance(max_passes, int) or max_passes <= 0
            or not isinstance(max_clause_visits, int) or max_clause_visits <= 0):
        raise ValueError("invalid Rust source preprocessing limits")
    source = tuple(tuple(clause) for clause in raw_clauses)
    for clause in source:
        for lit in clause:
            if not isinstance(lit, int) or lit == 0 or abs(lit) > nvars:
                raise ValueError("source literal out of range")
    try:
        from witnora_ve import simplify_source_native
    except ImportError as error:
        raise RuntimeError(
            "Rust source preprocessor unavailable; install the native PyO3 wheel"
        ) from error
    outcome = simplify_source_native(
        [list(clause) for clause in source], nvars,
        max_passes, max_clause_visits,
    )
    if outcome is None:
        return None
    simplified, passes, pairs = outcome
    if (not 1 <= passes <= max_passes
            or pairs < 0 or len(simplified) > max_clause_visits):
        raise RuntimeError("Rust source preprocessor violated invariants")
    return RustSourceSimplification(
        clauses=tuple(tuple(row) for row in simplified),
        passes=passes,
        consensus_pairs=pairs,
        original_clauses=len(source),
    )
