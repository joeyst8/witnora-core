"""Exact native GF(2) affine projection and left sparse Fourier expansion.

The Rust kernel uses arbitrary-precision integer numerators and a common
power-of-two denominator. This strict bridge exposes Python Fractions
and keeps the original Python implementation as an independent reference.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable


@dataclass(frozen=True)
class RustAffineSpectrum:
    projected_rows: tuple[tuple[int, int], ...] | None
    internal_free_variables: int
    spectrum: dict[int, Fraction]


def query_left_affine_in_rust(
    affine_rows: Iterable[tuple[int, int]],
    internal_variables: Iterable[int],
    boundary_variables: Iterable[int],
    *,
    max_terms: int = 4096,
) -> RustAffineSpectrum | None:
    """Exact affine projection+Fourier or None on spectral budget refusal."""
    internals = tuple(internal_variables)
    boundary = tuple(boundary_variables)
    source = tuple(affine_rows)
    if not isinstance(max_terms, int) or max_terms < 1:
        raise ValueError("invalid native Fourier spectrum term cap")
    if len(internals) + len(boundary) > 256:
        raise ValueError("native affine source has too many variables")
    for ids in (internals, boundary):
        if any(not isinstance(v, int) or v < 1 or v > 256 for v in ids):
            raise ValueError("invalid affine source variable ID")
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate affine source variable ID")
    if set(internals) & set(boundary):
        raise ValueError("affine internal/boundary sets overlap")
    allowed = sum(1 << (v - 1) for v in internals + boundary)
    for mask, rhs in source:
        if (not isinstance(mask, int) or mask < 0 or mask & ~allowed
                or rhs not in (0, 1)):
            raise ValueError("invalid native GF(2) affine row")
    try:
        from witnora_ve import affine_spectrum_native
    except ImportError as error:
        raise RuntimeError(
            "Rust affine Fourier kernel unavailable; install the PyO3 wheel"
        ) from error
    outcome = affine_spectrum_native(
        [(str(mask), rhs) for mask, rhs in source],
        list(internals), list(boundary), max_terms,
    )
    if outcome is None:
        return None
    raw_rows, free, raw_spectrum = outcome
    projected = (None if raw_rows is None else
                 tuple((int(mask), int(rhs)) for mask, rhs in raw_rows))
    spectrum = {
        int(mode): Fraction(int(num), int(den))
        for mode, num, den in raw_spectrum
    }
    if (not 0 <= free <= len(internals)
            or len(raw_spectrum) != len(spectrum)
            or len(spectrum) > max_terms
            or (projected is None and spectrum)):
        raise RuntimeError("Rust affine Fourier output violated invariants")
    return RustAffineSpectrum(projected, free, spectrum)
