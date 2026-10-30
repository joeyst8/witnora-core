"""Deterministic scalable exact-parity CNFs with fixed-size separators.

All equations share k boundary variables; each has private pair variables.
Removing the k boundary variables disconnects the private pairs.
"""
from __future__ import annotations

from .cnf import CNFFormula
from .xor import canonical_xor_cnf_clauses


def make_scaling_case(blocks_per_side: int, width: int) -> tuple[CNFFormula, dict]:
    if blocks_per_side < 1 or blocks_per_side > 128 or width not in (2, 3):
        raise ValueError("scaling case outside bounded experiment")
    boundary = tuple(range(1, width + 1))
    rows = set()
    for index in range(2 * blocks_per_side):
        a = 100 + 2 * index
        b = a + 1
        rows.update(canonical_xor_cnf_clauses((*boundary, a, b), index % 2))
    formula = CNFFormula.from_raw_clauses(rows)
    return formula, {
        "width": width,
        "blocks_per_side": blocks_per_side,
        "parity_equations": 2 * blocks_per_side,
        "expected_boundary": boundary,
    }
