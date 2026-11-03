"""Exact ANF common-zero counting using cached cofactors and component splits.

This is a performance experiment, not a polynomial-time algorithm.
The compilation maps ANF variable sets to integer bit masks; each
Boolean-ring monomial is a bit mask, and a polynomial is an XOR-set
of those masks. At a Shannon branch, cofactors are shared across
equation systems. When equation scopes disconnect, their numbers
of satisfying assignments multiply exactly.
"""
from __future__ import annotations

from dataclasses import dataclass

from witnora_core.violation_image_anf import (
    ANFCountingBudgetExceeded, Polynomial,
)

MaskPolynomial = frozenset[int]
MASK_ONE: MaskPolynomial = frozenset({0})


@dataclass(frozen=True)
class StructuredANFCountResult:
    satisfying_assignments: int
    unique_states: int
    memo_hits: int
    cofactor_hits: int
    cofactor_entries: int
    component_splits: int
    forced_assignments: int
    max_equations: int


def count_common_zeros_structured(
    equations: tuple[Polynomial, ...],
    nvars: int,
    *,
    max_states: int = 100_000,
) -> StructuredANFCountResult:
    """Count all common zeros, with a strict budget on unique states."""
    if nvars < 0 or max_states < 1:
        raise ValueError("invalid counting bounds")
    if any(v < 1 or v > nvars for p in equations for m in p for v in m):
        raise ValueError("equation uses an out-of-range variable")

    def compile_poly(poly: Polynomial) -> MaskPolynomial:
        return frozenset(
            sum(1 << (v - 1) for v in monomial)
            for monomial in poly
        )

    system = tuple(compile_poly(p) for p in equations)
    memo: dict[tuple[tuple[MaskPolynomial, ...], int], int] = {}
    cofactors: dict[tuple[MaskPolynomial, int, bool], MaskPolynomial] = {}
    stats = {"states": 0, "memo_hits": 0, "cofactor_hits": 0,
             "splits": 0, "forced": 0, "max_equations": 0}

    def canonical(polys: tuple[MaskPolynomial, ...]) -> tuple[MaskPolynomial, ...]:
        return tuple(sorted((p for p in set(polys) if p),
                            key=lambda p: tuple(sorted(p))))

    def cofactor(poly: MaskPolynomial, bit: int, value: bool) -> MaskPolynomial:
        key = (poly, bit, value)
        found = cofactors.get(key)
        if found is not None:
            stats["cofactor_hits"] += 1
            return found
        terms: set[int] = set()
        for monomial in poly:
            if monomial & bit:
                if not value:
                    continue
                monomial ^= bit
            if monomial in terms:
                terms.remove(monomial)
            else:
                terms.add(monomial)
        result = frozenset(terms)
        cofactors[key] = result
        return result

    def forced_unit(poly: MaskPolynomial) -> tuple[int, bool] | None:
        if len(poly) == 1:
            mono = next(iter(poly))
            if mono != 0 and mono & (mono - 1) == 0:
                return mono, False
        if len(poly) == 2 and 0 in poly:
            mono = next(m for m in poly if m)
            if mono & (mono - 1) == 0:
                return mono, True
        return None

    def groups(polys: tuple[MaskPolynomial, ...]) -> tuple[
        list[tuple[tuple[MaskPolynomial, ...], int]], int
    ]:
        # Union-find on variable scopes. Constant contradiction is
        # handled before calling this function.
        parent: dict[int, int] = {}

        def root(a: int) -> int:
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        scopes: list[int] = []
        active = 0
        for poly in polys:
            scope = 0
            for monomial in poly:
                scope |= monomial
            assert scope != 0
            scopes.append(scope)
            active |= scope
            first = scope & -scope
            parent.setdefault(first, first)
            tail = scope ^ first
            while tail:
                bit = tail & -tail
                parent.setdefault(bit, bit)
                ra, rb = root(first), root(bit)
                if ra != rb:
                    parent[rb] = ra
                tail ^= bit
        gathered: dict[int, list[MaskPolynomial]] = {}
        masks: dict[int, int] = {}
        for poly, scope in zip(polys, scopes):
            first = scope & -scope
            r = root(first)
            gathered.setdefault(r, []).append(poly)
            masks[r] = masks.get(r, 0) | scope
        return [(tuple(gathered[r]), masks[r]) for r in sorted(gathered)], active

    def solve(polys: tuple[MaskPolynomial, ...], remaining: int) -> int:
        current = canonical(polys)
        if MASK_ONE in current:
            return 0
        if not current:
            return 1 << remaining.bit_count()
        key = (current, remaining)
        if key in memo:
            stats["memo_hits"] += 1
            return memo[key]
        if stats["states"] >= max_states:
            raise ANFCountingBudgetExceeded(
                f"max symbolic states {max_states} exceeded")
        stats["states"] += 1
        stats["max_equations"] = max(stats["max_equations"], len(current))

        for eq in current:
            forced = forced_unit(eq)
            if forced is not None:
                bit, value = forced
                assert remaining & bit
                stats["forced"] += 1
                transformed = tuple(cofactor(p, bit, value) for p in current)
                answer = solve(transformed, remaining ^ bit)
                memo[key] = answer
                return answer

        components, active = groups(current)
        assert active & ~remaining == 0
        free = remaining & ~active
        if len(components) > 1:
            stats["splits"] += 1
            answer = 1 << free.bit_count()
            for part, scope in components:
                answer *= solve(part, scope)
                if answer == 0:
                    break
            memo[key] = answer
            return answer
        if free:
            answer = (1 << free.bit_count()) * solve(current, active)
            memo[key] = answer
            return answer

        appearances: dict[int, int] = {}
        for poly in current:
            for monomial in poly:
                rest = monomial
                while rest:
                    bit = rest & -rest
                    appearances[bit] = appearances.get(bit, 0) + 1
                    rest ^= bit
        chosen = max(appearances, key=lambda bit: (appearances[bit], -bit))
        rest_vars = remaining ^ chosen
        left = tuple(cofactor(p, chosen, False) for p in current)
        right = tuple(cofactor(p, chosen, True) for p in current)
        answer = solve(left, rest_vars) + solve(right, rest_vars)
        memo[key] = answer
        return answer

    result = solve(system, (1 << nvars) - 1)
    return StructuredANFCountResult(
        result, stats["states"], stats["memo_hits"],
        stats["cofactor_hits"], len(cofactors), stats["splits"],
        stats["forced"], stats["max_equations"],
    )
