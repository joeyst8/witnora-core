"""Symbolic GF(2) multilinear ANF for realizable clause-violation patterns.

Boolean assignment bits live in the quotient ring F_2[x_1,...,x_n] /
(x_i^2-x_i), so monomial multiplication is variable-set UNION.
For signed literal l, its false-indicator is x_v when l is negative
and 1+x_v when l is positive. The product over a clause is its exact
violation indicator. XORing selected clause polynomials gives the
exact parity check without enumerating source assignments.

The bounded recursive counter computes common zeros of ANF equations
using Shannon substitution/memoization. It is exponential in general
and is NOT a polynomial-time SAT solver or a complete TC-063 proof.
"""
from __future__ import annotations

from dataclasses import dataclass
from witnora_core.constraint_geometry import canonical_source
from witnora_core.gf2_sparse_row_basis import (SparseBasisCertificate, verify_sparse_parity_basis)
from witnora_core.sparse_parity_checks import SparseOddSketch, validate_sparse_odd_sketch

Monomial = frozenset[int]
Polynomial = frozenset[Monomial]
ZERO: Polynomial = frozenset()
ONE: Polynomial = frozenset({frozenset()})


class ANFCountingBudgetExceeded(RuntimeError):
    """Stopped before an unbounded symbolic branch search."""


def variable(var: int) -> Polynomial:
    if var < 1:
        raise ValueError("variable IDs must be positive")
    return frozenset({frozenset({var})})


def xor_polynomials(a: Polynomial, b: Polynomial) -> Polynomial:
    return a.symmetric_difference(b)


def multiply_polynomials(a: Polynomial, b: Polynomial) -> Polynomial:
    if not a or not b:
        return ZERO
    terms: set[Monomial] = set()
    for x in a:
        for y in b:
            monomial = x | y  # x_i**2=x_i on Boolean assignments
            if monomial in terms:
                terms.remove(monomial)
            else:
                terms.add(monomial)
    return frozenset(terms)


def false_literal_polynomial(lit: int) -> Polynomial:
    if lit == 0:
        raise ValueError("zero is not a source literal")
    x = variable(abs(lit))
    return x if lit < 0 else xor_polynomials(ONE, x)


def clause_violation_polynomial(clause: tuple[int, ...] | list[int]) -> Polynomial:
    result = ONE
    for lit in clause:
        result = multiply_polynomials(result, false_literal_polynomial(lit))
    return result


def source_violation_polynomials(
    source: list[list[int]] | tuple[tuple[int, ...], ...],
    nvars: int,
) -> tuple[Polynomial, ...]:
    cnf = canonical_source(source, nvars)
    return tuple(clause_violation_polynomial(clause) for clause in cnf)


def row_violation_polynomials(
    source: list[list[int]] | tuple[tuple[int, ...], ...],
    sketch: SparseOddSketch,
    *, basis: SparseBasisCertificate | None = None,
) -> tuple[Polynomial, ...]:
    cnf = validate_sparse_odd_sketch(source, sketch)
    if basis is not None:
        verify_sparse_parity_basis(sketch, basis)
    rows = sketch.rows if basis is None else basis.rows
    clauses = source_violation_polynomials(cnf, sketch.nvars)
    result = []
    for row in rows:
        equation = ZERO
        for j in row:
            equation = xor_polynomials(equation, clauses[j])
        result.append(equation)
    return tuple(result)


def evaluate_polynomial(poly: Polynomial, assignment_bits: int) -> bool:
    parity = False
    for monomial in poly:
        term = all(bool(assignment_bits & (1 << (v - 1)))
                   for v in monomial)
        parity ^= term
    return parity


def substitute(poly: Polynomial, variable_id: int, bit: bool) -> Polynomial:
    terms: set[Monomial] = set()
    for monomial in poly:
        if variable_id in monomial:
            if not bit:
                continue
            monomial = monomial - {variable_id}
        if monomial in terms:
            terms.remove(monomial)
        else:
            terms.add(monomial)
    return frozenset(terms)


def canonical_equations(equations: tuple[Polynomial, ...]) -> tuple[Polynomial, ...]:
    # Duplicate zero constraints do not affect the solution set.
    distinct = set(equations)
    distinct.discard(ZERO)
    return tuple(sorted(distinct, key=polynomial_key))


def polynomial_key(poly: Polynomial) -> tuple[tuple[int, ...], ...]:
    return tuple(sorted(tuple(sorted(monomial)) for monomial in poly))


@dataclass(frozen=True)
class ANFCountResult:
    satisfying_assignments: int
    unique_states: int
    memo_hits: int
    max_equations: int


def count_common_zeros(
    equations: tuple[Polynomial, ...],
    nvars: int,
    *, max_states: int = 100_000,
) -> ANFCountResult:
    """Exact bounded Shannon/memoized counter, not a polynomial algorithm."""
    if nvars < 0 or max_states < 1:
        raise ValueError("invalid counting bounds")
    if any(v < 1 or v > nvars for eq in equations for m in eq for v in m):
        raise ValueError("equation uses an out-of-range variable")
    memo: dict[tuple[tuple[Polynomial, ...], tuple[int, ...]], int] = {}
    stats = {"calls": 0, "hits": 0, "maximum": 0}

    def solve(system: tuple[Polynomial, ...], remaining: tuple[int, ...]) -> int:
        current = canonical_equations(system)
        if ONE in current:
            return 0
        if not current:
            return 1 << len(remaining)
        key = (current, remaining)
        if key in memo:
            stats["hits"] += 1
            return memo[key]
        if stats["calls"] >= max_states:
            raise ANFCountingBudgetExceeded(
                f"max symbolic states {max_states} exceeded")
        stats["calls"] += 1
        stats["maximum"] = max(stats["maximum"], len(current))
        appearances: dict[int, int] = {}
        for equation in current:
            for monomial in equation:
                for v in monomial:
                    appearances[v] = appearances.get(v, 0) + 1
        if not appearances:
            raise AssertionError("nontrivial equation lacks variables")
        chosen = max(appearances, key=lambda v: (appearances[v], -v))
        next_remaining = tuple(v for v in remaining if v != chosen)
        zero = tuple(substitute(eq, chosen, False) for eq in current)
        one = tuple(substitute(eq, chosen, True) for eq in current)
        result = solve(zero, next_remaining) + solve(one, next_remaining)
        memo[key] = result
        return result

    count = solve(equations, tuple(range(1, nvars + 1)))
    return ANFCountResult(count, stats["calls"], stats["hits"],
                          stats["maximum"])


@dataclass(frozen=True)
class ANFGeometry:
    nvars: int
    clause_count: int
    row_count: int
    raw_row_monomial_occurrences: int
    reduced_row_monomials: int
    zero_rows: int
    maximum_degree: int
    unique_nonzero_rows: int


def analyze_parity_anf(
    source: list[list[int]] | tuple[tuple[int, ...], ...],
    sketch: SparseOddSketch,
) -> ANFGeometry:
    cnf = validate_sparse_odd_sketch(source, sketch)
    clauses = source_violation_polynomials(cnf, sketch.nvars)
    equations = row_violation_polynomials(cnf, sketch)
    raw = sum(sum(len(clauses[j]) for j in row) for row in sketch.rows)
    kept = sum(len(eq) for eq in equations)
    max_degree = max((len(mon) for eq in equations for mon in eq),
                     default=0)
    return ANFGeometry(sketch.nvars, len(cnf), len(sketch.rows), raw, kept,
                       sum(not eq for eq in equations),
                       max_degree, len(set(equations) - {ZERO}))
