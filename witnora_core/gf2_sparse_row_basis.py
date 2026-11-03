"""Sparse GF(2) parity-row basis with independently checkable equivalence.

Select an independent SUBSET of the ORIGINAL small parity rows, rather
than replacing them with dense RREF rows. For each dropped row, produce a
bitset identifying retained rows whose XOR exactly reconstructs it.

This proves all original row constraints iff all retained constraints,
for EVERY violation vector, with NO source-assignment enumeration. It
does not imply source-CNF equivalence for an inexact parity sketch.
"""
from __future__ import annotations

from dataclasses import dataclass

from witnora_core.sparse_parity_checks import SparseOddSketch


@dataclass(frozen=True)
class SparseBasisCertificate:
    clause_count: int
    original_row_count: int
    selected_indices: tuple[int, ...]
    rows: tuple[tuple[int, ...], ...]
    expansions: tuple[int, ...]
    ordering: str

    @property
    def rank(self) -> int:
        return len(self.rows)

    @property
    def nullity(self) -> int:
        return self.clause_count - self.rank


def row_mask(row: tuple[int, ...]) -> int:
    result = 0
    for j in row:
        result ^= 1 << j
    return result


def _xor_selected(mask: int, rows: tuple[int, ...]) -> int:
    result = 0
    for j, row in enumerate(rows):
        if mask & (1 << j):
            result ^= row
    return result


def build_sparse_parity_basis(
    sketch: SparseOddSketch, *, ordering: str = "shortest_first",
) -> SparseBasisCertificate:
    """Deterministic row-space basis without growing row widths."""
    if ordering not in ("shortest_first", "source_order"):
        raise ValueError("unsupported row ordering")
    m = sketch.clause_count
    if m < 0 or sketch.max_row_width < 1:
        raise ValueError("invalid sketch dimension")
    for row in sketch.rows:
        if (tuple(sorted(set(row))) != row or
                len(row) > sketch.max_row_width or
                any(j < 0 or j >= m for j in row)):
            raise ValueError("invalid parity row")
    order = list(range(len(sketch.rows)))
    if ordering == "shortest_first":
        order.sort(key=lambda j: (len(sketch.rows[j]),
                                   sketch.rows[j], j))
    # Pivot -> reduced row and its XOR expression in selected ORIGINAL rows.
    pivots: dict[int, tuple[int, int]] = {}
    chosen: list[int] = []
    coefficients = [0] * len(sketch.rows)
    for rid in order:
        remaining = row_mask(sketch.rows[rid])
        expression = 0
        while remaining:
            pivot = (remaining & -remaining).bit_length() - 1
            found = pivots.get(pivot)
            if found is None:
                basis_index = len(chosen)
                chosen.append(rid)
                expression ^= 1 << basis_index
                pivots[pivot] = (remaining, expression)
                break
            reduced, retained_expression = found
            remaining ^= reduced
            expression ^= retained_expression
        coefficients[rid] = expression
    certificate = SparseBasisCertificate(
        clause_count=m, original_row_count=len(sketch.rows),
        selected_indices=tuple(chosen),
        rows=tuple(sketch.rows[j] for j in chosen),
        expansions=tuple(coefficients),
        ordering=ordering,
    )
    verify_sparse_parity_basis(sketch, certificate)
    return certificate


def verify_sparse_parity_basis(
    sketch: SparseOddSketch, cert: SparseBasisCertificate,
) -> None:
    """Independent reconstruction and linear independence, fail closed."""
    if (cert.clause_count != sketch.clause_count or
            cert.original_row_count != len(sketch.rows) or
            len(cert.expansions) != len(sketch.rows) or
            cert.ordering not in ("shortest_first", "source_order") or
            len(cert.selected_indices) != len(cert.rows) or
            len(set(cert.selected_indices)) != len(cert.selected_indices) or
            any(j < 0 or j >= len(sketch.rows)
                for j in cert.selected_indices)):
        raise ValueError("basis dimensions or indexing invalid")
    if tuple(sketch.rows[j] for j in cert.selected_indices) != cert.rows:
        raise ValueError("a retained row differs from the source sketch")
    if any(len(row) > sketch.max_row_width for row in cert.rows):
        raise ValueError("basis row scope too large")
    rowbits = tuple(row_mask(row) for row in cert.rows)
    originals = tuple(row_mask(row) for row in sketch.rows)
    limit = 1 << len(rowbits)
    for original, expansion in zip(originals, cert.expansions):
        if expansion < 0 or expansion >= limit:
            raise ValueError("out-of-range row reconstruction coefficients")
        if _xor_selected(expansion, rowbits) != original:
            raise ValueError("invalid GF(2) reconstruction witness")
    for basis_index, source_id in enumerate(cert.selected_indices):
        if cert.expansions[source_id] != 1 << basis_index:
            raise ValueError("retained row has invalid identity witness")
    # Independent rank check on retained masks.
    echelon: dict[int, int] = {}
    for mask in rowbits:
        while mask:
            p = (mask & -mask).bit_length() - 1
            if p not in echelon:
                echelon[p] = mask
                break
            mask ^= echelon[p]
        else:
            raise ValueError("claimed basis has linearly dependent rows")


def accepts_masks(mask: int, rows: tuple[tuple[int, ...], ...]) -> bool:
    return all((mask & row_mask(row)).bit_count() % 2 == 0
               for row in rows)
