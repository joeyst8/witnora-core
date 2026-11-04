"""R-008 strict one-call native source-CNF model-count bridge.

All normalization, XOR recognition, GF(2) projection, Fourier contraction,
and right CNF coefficients execute in Rust. There is no Python counting
fallback. The extension returns a decimal integer for arbitrary precision.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class RustFusedSourceResult:
    models: int
    extracted_affine_rows: int
    residual_clauses: int
    boundary_variables: int
    internal_variables: int
    internal_free_variables: int
    left_fourier_terms: int
    right_violation_terms: int
    right_components: int
    source_preprocess_skipped: bool
    source_preprocess_passes: int
    right_subset_operations: int


def count_source_fused_in_rust(
    raw_clauses: Iterable[Iterable[int]],
    nvars: int,
    *,
    source_preprocessor: str = "rust_adaptive",
    max_preprocess_passes: int = 64,
    max_preprocess_clause_visits: int = 1000000,
    max_spectrum_terms: int = 4096,
    max_inclusion_subsets: int = 4096,
    max_rust_coefficient_operations: int = 2000000,
) -> RustFusedSourceResult | None:
    """Return exact models and diagnostics, or None on a native budget cap.

    ImportError is intentional if the native wheel is unavailable. Invalid
    literals or budgets produce an error; there is no guessed model count.
    """
    if not isinstance(nvars, int) or isinstance(nvars, bool) or not 0 <= nvars <= 256:
        raise ValueError("R-008 supports nvars in 0..256")
    if source_preprocessor not in ("none", "rust_consensus", "rust_adaptive"):
        raise ValueError("unknown exact Rust source preprocessor")
    for cap in (max_preprocess_passes, max_preprocess_clause_visits,
                max_spectrum_terms, max_inclusion_subsets,
                max_rust_coefficient_operations):
        if not isinstance(cap, int) or isinstance(cap, bool) or cap < 0:
            raise ValueError("native resource caps must be nonnegative integers")
    clauses: list[list[int]] = []
    for clause in raw_clauses:
        items = list(clause)
        for lit in items:
            if not isinstance(lit, int) or isinstance(lit, bool) or lit == 0 or abs(lit) > nvars:
                raise ValueError("source literal out of range")
        clauses.append(items)

    from witnora_ve import count_source_native
    got = count_source_native(
        clauses, nvars, source_preprocessor, max_preprocess_passes,
        max_preprocess_clause_visits, max_spectrum_terms,
        max_inclusion_subsets, max_rust_coefficient_operations,
    )
    if got is None:
        return None
    (models, rows, residual, boundary, internal, internal_free, left_terms,
     right_terms, components, skipped, passes, operations) = got
    return RustFusedSourceResult(
        models=int(models), extracted_affine_rows=int(rows),
        residual_clauses=int(residual), boundary_variables=int(boundary),
        internal_variables=int(internal), internal_free_variables=int(internal_free),
        left_fourier_terms=int(left_terms), right_violation_terms=int(right_terms),
        right_components=int(components), source_preprocess_skipped=bool(skipped),
        source_preprocess_passes=int(passes), right_subset_operations=int(operations),
    )
