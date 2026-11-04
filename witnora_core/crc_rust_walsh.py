"""Opt-in exact native right-CNF Walsh coefficient batch calculations.

The Rust kernel computes dyadic fractions by signed arbitrary-precision
integers. The output is converted to Python Fraction only at the trust
boundary; the original Python inclusion-exclusion engine remains the
reference for randomized exact differential tests.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable


@dataclass(frozen=True)
class RustWalshBatch:
    coefficients: dict[int, Fraction]
    compatible_terms: int
    components: int
    subset_operations: int


def query_right_walsh_in_rust(
    normalized_clauses: tuple[tuple[int, int], ...] | None,
    boundary_variables: Iterable[int],
    modes: Iterable[int],
    *,
    max_subsets: int = 4096,
    max_operations: int = 2000000,
) -> RustWalshBatch | None:
    """Exact coefficients or None on native IE subset/operation budget."""
    boundary = tuple(boundary_variables)
    requested = tuple(modes)
    if (not isinstance(max_subsets, int) or max_subsets < 0
            or not isinstance(max_operations, int) or max_operations < 1
            or len(boundary) > 256):
        raise ValueError("invalid native Walsh budgets")
    if any(not isinstance(v, int) or v < 1 or v > 256 for v in boundary):
        raise ValueError("invalid native Walsh boundary")
    if len(set(boundary)) != len(boundary):
        raise ValueError("duplicate native Walsh boundary ID")
    allowed = sum(1 << (v - 1) for v in boundary)
    if any(not isinstance(mode, int) or mode < 0 or mode & ~allowed
           for mode in requested):
        raise ValueError("invalid right Walsh mode")
    if normalized_clauses is not None:
        for zeros, ones in normalized_clauses:
            if (not isinstance(zeros, int) or not isinstance(ones, int)
                    or zeros < 0 or ones < 0 or zeros & ones
                    or not (zeros | ones) or (zeros | ones) & ~allowed):
                raise ValueError("invalid normalized clause mask")
    try:
        from witnora_ve import right_walsh_native
    except ImportError as error:
        raise RuntimeError(
            "Rust exact Walsh engine unavailable; install the PyO3 wheel"
        ) from error
    encoded = (None if normalized_clauses is None else
               [(str(z), str(o)) for z, o in normalized_clauses])
    outcome = right_walsh_native(
        encoded, list(boundary), [str(m) for m in requested],
        max_subsets, max_operations,
    )
    if outcome is None:
        return None
    encoded_coefficients, terms, components, operations = outcome
    if (len(encoded_coefficients) != len(requested)
            or terms < 0 or components < 0
            or operations < 0 or operations > max_operations):
        raise RuntimeError("native right Walsh result violated resource invariants")
    coefficients = {
        mode: Fraction(int(num), int(den))
        for mode, (num, den) in zip(requested, encoded_coefficients)
    }
    return RustWalshBatch(coefficients, terms, components, operations)
