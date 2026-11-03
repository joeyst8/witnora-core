"""Exact bounded Walsh coefficient queries by shared Shannon recursion.

For a CNF g over boundary variables, computes for selected modes T:
    W_g(T) = sum_(s in {0,1}^boundary) [g(s)] (-1)^parity(T & s)
and returns normalized coefficients W_g(T) / 2^|boundary|.

Unlike subset inclusion-exclusion this may handle many overlapping
clauses, but worst-case state growth remains exponential. It is ordinary
memoized weighted model counting; no general SAT speedup is claimed.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable


@dataclass(frozen=True)
class WalshQueryResult:
    coefficients: dict[int, Fraction]
    states: int
    memo_hits: int


class WalshQueryBudgetExceeded(RuntimeError):
    """Search stopped before supplying an unverified coefficient."""


def _bit_literals(zeros: int, ones: int) -> tuple[int, ...]:
    lits: list[int] = []
    for m, polarity in ((zeros, 1), (ones, -1)):
        while m:
            bit = m & -m
            lits.append(polarity * bit.bit_length())
            m ^= bit
    return tuple(sorted(lits, key=lambda lit: (abs(lit), lit)))


def _canonical(clauses: Iterable[tuple[int, ...]]) -> tuple[tuple[int, ...], ...]:
    found = set(clauses)
    if () in found:
        return ((),)
    return tuple(sorted(found, key=lambda c: (len(c), c)))


def _cofactor(
    clauses: tuple[tuple[int, ...], ...],
    variable_id: int,
    value: bool,
) -> tuple[tuple[int, ...], ...]:
    transformed = []
    for clause in clauses:
        if any(abs(lit) == variable_id and (lit > 0) == value for lit in clause):
            continue  # Satisfied clause disappears.
        kept = tuple(lit for lit in clause if abs(lit) != variable_id)
        if not kept:
            return ((),)
        transformed.append(kept)
    return _canonical(transformed)


def query_walsh_coefficients(
    normalized_violations: tuple[tuple[int, int], ...] | None,
    boundary_variables: tuple[int, ...],
    modes: tuple[int, ...],
    *,
    max_states: int,
) -> WalshQueryResult | None:
    """Exact selected coefficients, or None when state budget is hit.

    Each (zeros,ones) pair is the falsifying partial assignment for
    one CNF clause. None means an empty contradictory source clause.
    All modes and variables use global positive-ID bit positions.
    """
    if max_states < 1:
        raise ValueError("max_states must be positive")
    boundary_mask = 0
    for variable in boundary_variables:
        if variable < 1 or variable > 256:
            raise ValueError("prototype variable IDs outside 1..256")
        bit = 1 << (variable - 1)
        if boundary_mask & bit:
            raise ValueError("duplicate boundary variable")
        boundary_mask |= bit
    if any(mode < 0 or (mode & ~boundary_mask) for mode in modes):
        raise ValueError("Walsh mode mentions nonboundary variables")
    if normalized_violations is None:
        return WalshQueryResult({mode: Fraction() for mode in modes}, 0, 0)

    clauses = _canonical(_bit_literals(z, o) for z, o in normalized_violations)
    stats = {"states": 0, "hits": 0}
    memo: dict[tuple[tuple[tuple[int, ...], ...], int], tuple[int, ...]] = {}

    def solve(
        current: tuple[tuple[int, ...], ...], remaining: int,
    ) -> tuple[int, ...]:
        key = (current, remaining)
        if key in memo:
            stats["hits"] += 1
            return memo[key]
        if stats["states"] >= max_states:
            raise WalshQueryBudgetExceeded
        stats["states"] += 1
        if () in current:
            result = (0,) * len(modes)
        elif not current:
            free_count = remaining.bit_count()
            result = tuple(0 if (mode & remaining) else (1 << free_count)
                           for mode in modes)
        else:
            unit = min((abs(c[0]) for c in current if len(c) == 1), default=None)
            if unit is not None:
                chosen = unit
            else:
                appearances: dict[int, int] = {}
                for clause in current:
                    for lit in clause:
                        v = abs(lit)
                        appearances[v] = appearances.get(v, 0) + 1
                chosen = min(appearances, key=lambda v: (-appearances[v], v))
            bit = 1 << (chosen - 1)
            assert remaining & bit
            remaining_next = remaining ^ bit
            zeros = solve(_cofactor(current, chosen, False), remaining_next)
            ones = solve(_cofactor(current, chosen, True), remaining_next)
            result = tuple(
                a - b if mode & bit else a + b
                for mode, a, b in zip(modes, zeros, ones)
            )
        memo[key] = result
        return result

    try:
        weighted = solve(clauses, boundary_mask)
    except WalshQueryBudgetExceeded:
        return None
    divisor = 1 << len(boundary_variables)
    return WalshQueryResult(
        {mode: Fraction(value, divisor) for mode, value in zip(modes, weighted)},
        stats["states"], stats["hits"],
    )
