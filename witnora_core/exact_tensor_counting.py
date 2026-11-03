"""Exact polynomial-valued factor elimination for small SAT test instances.

This is a REAL contraction engine (binary factor tables, exact integer
polynomial arithmetic), not a graph-width diagnostic. It is purposely
limited to bounded intermediate scopes; it is NOT a scalable SAT solver.

Source CNF: sum_x product_j 1[C_j(x)].
Aux parity: sum_(x,v) product_j 1[v_j=violation(C_j(x))]
                   product_R 1[XOR_(j in R) v_j=0] * t^(sum_j v_j).
The t^0 coefficient equals #SAT even if parity accepts nonmodels.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from witnora_core.constraint_geometry import canonical_source
from witnora_core.factor_elimination_orders import elimination_order
from witnora_core.sparse_parity_checks import (
    SparseOddSketch, validate_sparse_odd_sketch,
)

Poly = tuple[int, ...]
ZERO: Poly = ()
ONE: Poly = (1,)


class ContractionBudgetExceeded(RuntimeError):
    """A proposed contraction scope or work limit is too large."""


@dataclass(frozen=True)
class Factor:
    scope: tuple[int, ...]
    values: dict[int, Poly]


@dataclass(frozen=True)
class ContractionResult:
    coefficients: Poly
    max_bucket_variables: int
    visited_assignments: int
    peak_table_entries: int


def poly_add(a: Poly, b: Poly) -> Poly:
    size = max(len(a), len(b))
    if not size:
        return ZERO
    out = [(a[i] if i < len(a) else 0) +
           (b[i] if i < len(b) else 0) for i in range(size)]
    while out and not out[-1]:
        out.pop()
    return tuple(out)


def poly_mul(a: Poly, b: Poly) -> Poly:
    if not a or not b:
        return ZERO
    out = [0] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        if ai:
            for j, bj in enumerate(b):
                if bj:
                    out[i + j] += ai * bj
    while out and not out[-1]:
        out.pop()
    return tuple(out)


def _lit_true(lit: int, scope: tuple[int, ...], bits: int) -> bool:
    value = bool(bits & (1 << scope.index(abs(lit))))
    return value == (lit > 0)


def _clause_value(clause: tuple[int, ...],
                  scope: tuple[int, ...], bits: int) -> bool:
    return any(_lit_true(lit, scope, bits) for lit in clause)


def source_factors(source: list[list[int]] | tuple[tuple[int, ...], ...],
                   nvars: int) -> list[Factor]:
    cnf = canonical_source(source, nvars)
    factors = []
    for clause in cnf:
        scope = tuple(sorted({abs(lit) for lit in clause}))
        table = {bits: ONE for bits in range(1 << len(scope))
                 if _clause_value(clause, scope, bits)}
        factors.append(Factor(scope, table))
    return factors


def auxiliary_factors(
    source: list[list[int]] | tuple[tuple[int, ...], ...],
    sketch: SparseOddSketch,
) -> list[Factor]:
    cnf = validate_sparse_odd_sketch(source, sketch)
    n = sketch.nvars
    factors: list[Factor] = []
    for j, clause in enumerate(cnf):
        aux_id = n + j + 1
        scope = tuple(sorted({abs(lit) for lit in clause} | {aux_id}))
        v_pos = scope.index(aux_id)
        table = {}
        for bits in range(1 << len(scope)):
            violated = not _clause_value(clause, scope, bits)
            if bool(bits & (1 << v_pos)) == violated:
                table[bits] = ONE
        factors.append(Factor(scope, table))
        # The monomial weight t^v_j is a separate unary factor.
        factors.append(Factor((aux_id,), {0: ONE, 1: (0, 1)}))
    for row in sketch.rows:
        scope = tuple(sorted(n + j + 1 for j in row))
        table = {bits: ONE for bits in range(1 << len(scope))
                 if bits.bit_count() % 2 == 0}
        factors.append(Factor(scope, table))
    return factors


def _project(bits: int, positions: tuple[int, ...]) -> int:
    result = 0
    for j, parent_pos in enumerate(positions):
        result |= ((bits >> parent_pos) & 1) << j
    return result


def contract_factors(
    factors: list[Factor], nvars: int, *,
    order: tuple[int, ...] | None = None,
    max_bucket_variables: int = 12,
    max_visited_assignments: int = 2_000_000,
) -> ContractionResult:
    """Exact elimination with explicit scope and arithmetic-work fail-closed caps."""
    if nvars < 0 or max_bucket_variables < 1 or max_visited_assignments < 1:
        raise ValueError("invalid contraction bounds")
    if order is None:
        order = elimination_order([set(f.scope) for f in factors], nvars,
                                  nsource=nvars).order
    if len(order) != nvars or set(order) != set(range(1, nvars + 1)):
        raise ValueError("order must permute all variable IDs")
    for f in factors:
        if tuple(sorted(set(f.scope))) != f.scope:
            raise ValueError("factor scope must be sorted and distinct")
        if any(v < 1 or v > nvars for v in f.scope):
            raise ValueError("factor outside declared variable domain")
        if any(bits < 0 or bits >= 1 << len(f.scope) for bits in f.values):
            raise ValueError("factor assignment outside local scope")
    active_factors = list(factors)
    peak_entries = sum(len(f.values) for f in active_factors)
    max_width = visited = 0
    for var in order:
        bucket = [f for f in active_factors if var in f.scope]
        others = [f for f in active_factors if var not in f.scope]
        union_scope = tuple(sorted({var} |
                                   {v for f in bucket for v in f.scope}))
        width = len(union_scope)
        max_width = max(max_width, width)
        work = 1 << width
        if (width > max_bucket_variables or
                visited + work > max_visited_assignments):
            raise ContractionBudgetExceeded(
                f"eliminating {var} needs {width} variables, {work} states; "
                f"visited={visited}, limit={max_visited_assignments}")
        visited += work
        var_pos = union_scope.index(var)
        remaining = tuple(v for v in union_scope if v != var)
        placements = [tuple(union_scope.index(v) for v in f.scope)
                      for f in bucket]
        low = (1 << var_pos) - 1
        table: dict[int, Poly] = {}
        for outer in range(1 << len(remaining)):
            total = ZERO
            for var_bit in (0, 1):
                full = ((outer & low) |
                        (var_bit << var_pos) |
                        ((outer >> var_pos) << (var_pos + 1)))
                product = ONE
                for f, positions in zip(bucket, placements):
                    product = poly_mul(
                        product, f.values.get(_project(full, positions), ZERO))
                    if not product:
                        break
                total = poly_add(total, product)
            if total:
                table[outer] = total
        active_factors = others + [Factor(remaining, table)]
        peak_entries = max(peak_entries,
                           sum(len(f.values) for f in active_factors))
    result = ONE
    for f in active_factors:
        if f.scope:
            raise AssertionError("uneliminated nonconstant factor")
        result = poly_mul(result, f.values.get(0, ZERO))
    return ContractionResult(result, max_width, visited, peak_entries)


def count_source_exact(
    source: list[list[int]] | tuple[tuple[int, ...], ...], nvars: int, **budget,
) -> ContractionResult:
    return contract_factors(source_factors(source, nvars), nvars, **budget)


def count_auxiliary_weight_polynomial(
    source: list[list[int]] | tuple[tuple[int, ...], ...],
    sketch: SparseOddSketch, **budget,
) -> ContractionResult:
    return contract_factors(
        auxiliary_factors(source, sketch),
        sketch.nvars + sketch.clause_count,
        **budget,
    )
