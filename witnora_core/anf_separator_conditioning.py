"""Bounded exact separator-conditioned ANF common-zero counting.

If removing a small variable set S disconnects the equation-scope
hypergraph, Shannon-condition on all Boolean assignments to S.
For each branch add *equations fixing S* to avoid counting those
separator variables as free, then use the exact structured ANF
counter. Sum the branch counts. This is exponential in |S| and
does not promise a speedup on arbitrary connected formulas.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from witnora_core.anf_structured_counter import count_common_zeros_structured
from witnora_core.violation_image_anf import (
    ANFCountingBudgetExceeded, ONE, Polynomial, variable, xor_polynomials,
)


@dataclass(frozen=True)
class SeparatorCountResult:
    satisfying_assignments: int
    separator: tuple[int, ...]
    separator_found: bool
    branches: int
    total_unique_states: int
    total_component_splits: int
    total_cofactor_hits: int
    total_forced_assignments: int
    separator_candidates_checked: int


def polynomial_scopes(equations: tuple[Polynomial, ...]) -> tuple[int, ...]:
    """Variable bit masks for every GF(2) equation."""
    scopes: list[int] = []
    for poly in equations:
        scope = 0
        for monomial in poly:
            for var in monomial:
                if var < 1:
                    raise ValueError("variable IDs must be positive")
                scope |= 1 << (var - 1)
        scopes.append(scope)
    return tuple(scopes)


def residual_component_sizes(
    scopes: tuple[int, ...], removed_mask: int,
    *, backend="python",
) -> tuple[int, ...]:
    """Connected component sizes after conditioning away variables."""
    if backend == "rust":
        from witnora_ve import anf_residual_component_sizes_native
        return tuple(anf_residual_component_sizes_native(
            [str(scope) for scope in scopes], str(removed_mask)))
    if backend != "python":
        raise ValueError("unknown ANF separator backend")
    parent: dict[int, int] = {}

    def root(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for scope in scopes:
        remaining = scope & ~removed_mask
        if not remaining:
            continue
        anchor = remaining & -remaining
        parent.setdefault(anchor, anchor)
        remaining ^= anchor
        while remaining:
            bit = remaining & -remaining
            parent.setdefault(bit, bit)
            ra, rb = root(anchor), root(bit)
            if ra != rb:
                parent[rb] = ra
            remaining ^= bit
    sizes: dict[int, int] = {}
    for bit in parent:
        r = root(bit)
        sizes[r] = sizes.get(r, 0) + 1
    return tuple(sorted(sizes.values(), reverse=True))


def find_bounded_separator(
    equations: tuple[Polynomial, ...],
    nvars: int,
    *,
    max_separator_size: int = 2,
    max_candidate_checks: int = 1_000,
    backend="python",
) -> tuple[tuple[int, ...] | None, int]:
    """Find a small set whose removal produces >=2 nonempty components.

    Search is deterministic and budgeted. No separator returned means
    NONE FOUND BY THIS SEARCH, not a lower-bound proof that none exists.
    """
    if nvars < 0 or max_separator_size < 0 or max_candidate_checks < 1:
        raise ValueError("invalid separator search bounds")
    if backend == "rust":
        from witnora_ve import anf_find_bounded_separator_native
        selected, checked = anf_find_bounded_separator_native(
            [[list(sorted(mon)) for mon in sorted(eq, key=lambda m: tuple(sorted(m)))]
             for eq in equations], nvars, max_separator_size, max_candidate_checks)
        return (tuple(selected) if selected is not None else None), checked
    if backend != "python":
        raise ValueError("unknown ANF separator search backend")
    scopes = polynomial_scopes(equations)
    active = 0
    for scope in scopes:
        active |= scope
    if active >> nvars:
        raise ValueError("equation uses an out-of-range variable")
    if len(residual_component_sizes(scopes, 0, backend=backend)) != 1:
        return None, 0

    variables = tuple(v for v in range(1, nvars + 1)
                      if active & (1 << (v - 1)))
    degree = {v: sum(bool(scope & (1 << (v - 1))) for scope in scopes)
              for v in variables}
    checked = 0
    for k in range(1, min(max_separator_size, len(variables)) + 1):
        # All singleton candidates; for larger separators all variables
        # when <=32, otherwise a deliberately limited high-degree pool.
        if k == 1 or len(variables) <= 32:
            pool = variables
        else:
            pool = tuple(sorted(sorted(variables,
                                       key=lambda v: (-degree[v], v))[:24]))
        best: tuple[tuple[int, int, tuple[int, ...]], tuple[int, ...]] | None = None
        for selected in combinations(pool, k):
            if checked >= max_candidate_checks:
                return (best[1] if best else None), checked
            checked += 1
            removed = sum(1 << (v - 1) for v in selected)
            sizes = residual_component_sizes(scopes, removed, backend=backend)
            if len(sizes) < 2:
                continue
            # Prefer balanced decompositions, then more components.
            score = (sizes[0], -len(sizes), selected)
            if best is None or score < best[0]:
                best = (score, selected)
        if best is not None:
            return best[1], checked
    return None, checked


def count_common_zeros_conditioned(
    equations: tuple[Polynomial, ...],
    nvars: int,
    *,
    max_states: int = 100_000,
    max_separator_size: int = 2,
    max_candidate_checks: int = 1_000,
    backend="python",
) -> SeparatorCountResult:
    """Exact #solutions, using small-separator conditioning if found."""
    if max_states < 1:
        raise ValueError("max_states must be positive")
    selected, checks = find_bounded_separator(
        equations, nvars, max_separator_size=max_separator_size,
        max_candidate_checks=max_candidate_checks, backend=backend)
    if selected is None:
        r = count_common_zeros_structured(equations, nvars,
                                           max_states=max_states)
        return SeparatorCountResult(
            r.satisfying_assignments, (), False, 1, r.unique_states,
            r.component_splits, r.cofactor_hits, r.forced_assignments,
            checks)

    total = 0
    states = 0
    splits = 0
    hits = 0
    forced = 0
    for assignment in range(1 << len(selected)):
        pins: list[Polynomial] = []
        for i, v in enumerate(selected):
            bit = bool(assignment & (1 << i))
            # x_v=0 means the polynomial x_v must vanish;
            # x_v=1 means the polynomial 1+x_v must vanish.
            pin = variable(v)
            pins.append(xor_polynomials(ONE, pin) if bit else pin)
        budget = max_states - states
        if budget < 1:
            raise ANFCountingBudgetExceeded(
                f"max total symbolic states {max_states} exceeded")
        r = count_common_zeros_structured(
            equations + tuple(pins), nvars, max_states=budget)
        total += r.satisfying_assignments
        states += r.unique_states
        splits += r.component_splits
        hits += r.cofactor_hits
        forced += r.forced_assignments
    return SeparatorCountResult(total, selected, True, 1 << len(selected),
                                states, splits, hits, forced, checks)
