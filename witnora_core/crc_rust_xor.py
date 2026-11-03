"""Opt-in exact Rust extraction of complete source CNF k-XOR blocks.

The PyO3 native function returns arbitrary-precision equation masks as
decimal strings. This wrapper validates the boundaries and presents the
same shapes as the independent Python reference `extract_exact_small_xors`.
"""
from __future__ import annotations

from typing import Iterable


def extract_small_xors_in_rust(
    raw_clauses: Iterable[Iterable[int]], nvars: int,
) -> tuple[tuple[tuple[int, int], ...], tuple[tuple[int, ...], ...]]:
    if not isinstance(nvars, int) or not 0 <= nvars <= 256:
        raise ValueError("native source extractor supports nvars in 0..256")
    source = tuple(tuple(c) for c in raw_clauses)
    for clause in source:
        for lit in clause:
            if not isinstance(lit, int) or lit == 0 or abs(lit) > nvars:
                raise ValueError("source literal out of range")
    try:
        from witnora_ve import extract_small_xors_native
    except ImportError as error:
        raise RuntimeError(
            "Rust small-XOR source extractor unavailable; install the PyO3 wheel"
        ) from error
    raw_rows, residual = extract_small_xors_native(
        [list(c) for c in source], nvars)
    rows = tuple((int(mask), int(rhs)) for mask, rhs in raw_rows)
    clauses = tuple(tuple(c) for c in residual)
    if (any(mask < 0 or mask >= (1 << nvars) or rhs not in (0, 1)
            for mask, rhs in rows)
            or any(any(abs(lit) < 1 or abs(lit) > nvars for lit in c)
                   for c in clauses)):
        raise RuntimeError("Rust small-XOR extractor violated invariants")
    return rows, clauses
