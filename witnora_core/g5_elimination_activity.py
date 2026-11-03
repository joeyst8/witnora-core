"""Research-only G5 elimination-activity hints for TC-063 separators.

This consumes row-XOR operations already emitted by Gaussian elimination.
It neither infers UNSAT nor promotes a separator: candidates still require
the existing exact G14 component and Lean proof checks.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from itertools import combinations
from typing import Any


def _support(value: Any) -> set[int]:
    if not isinstance(value, dict) or not isinstance(value.get("coefficients"), list):
        raise ValueError("G5 operation row must contain a coefficient list")
    coefficients = value["coefficients"]
    if any(type(v) is not int or v <= 0 for v in coefficients):
        raise ValueError("G5 row coefficients must be positive integer IDs")
    if len(set(coefficients)) != len(coefficients):
        raise ValueError("G5 row coefficients must be unique")
    return set(coefficients)


def activity_from_g5_operations(
    operations: Iterable[Mapping[str, Any]],
    variables: Iterable[int],
) -> dict[str, Any]:
    """Rank variables by participation in actual ADD_ROW_XOR operations.

    The touch score counts once per operation for each variable in the
    union of the target's *before* support and its source support.
    Cancellation is a secondary tie-breaker. This is an experimental
    heuristic, not a verified predictor of a useful separator.
    """
    universe = tuple(sorted(set(variables)))
    if any(type(v) is not int or v <= 0 for v in universe):
        raise ValueError("variables must be positive integer IDs")
    touches: Counter[int] = Counter()
    cancellations: Counter[int] = Counter()
    xor_operations = 0
    for operation in operations:
        kind = operation.get("operation")
        if kind == "SWAP_ROWS":
            continue
        if kind != "ADD_ROW_XOR":
            raise ValueError("unsupported G5 operation kind")
        before = _support(operation.get("before"))
        source = _support(operation.get("source"))
        if not before | source <= set(universe):
            raise ValueError("operation has variable outside declared universe")
        xor_operations += 1
        touches.update(before | source)
        cancellations.update(before & source)
    ranked = tuple(
        sorted(universe, key=lambda v: (-touches[v], -cancellations[v], v))
    )
    return {
        "ranked_variables": ranked,
        "touches": {v: touches[v] for v in universe},
        "cancellations": {v: cancellations[v] for v in universe},
        "xor_operations": xor_operations,
        "top_pair": tuple(ranked[:2]) if len(ranked) >= 2 else (),
        "status": "DIAGNOSTIC_ONLY",
    }


def ranked_pair_candidates(activity: Mapping[str, Any], limit: int | None = None):
    """Enumerate diagnostic two-variable pairs, high-activity first.

    Even if a caller uses this ordering for G14 search, it must retain
    an exhaustive fallback over every pair.
    """
    ranked = tuple(activity["ranked_variables"])
    if limit is not None:
        if type(limit) is not int or limit < 0:
            raise ValueError("limit must be a nonnegative integer")
        ranked = ranked[:limit]
    return tuple(combinations(ranked, 2))


def pairwise_cross_merge_activity(
    operations: Iterable[Mapping[str, Any]],
    variables: Iterable[int],
) -> dict[str, Any]:
    """Rank unordered variable pairs by opposite-side XOR interactions.

    A pair gains one point when one variable occurs only in the target
    before the XOR and the other only in the source. These two surviving
    variables are brought into the derived row by the operation. This
    is *not* a sound separator inference; every proposed pair still
    needs independent graph and G14 checks.

    Traversal costs O(sum |target_only| * |source_only|) across operations,
    plus sorting all O(n^2) candidate pairs.
    """
    universe = tuple(sorted(set(variables)))
    if any(type(v) is not int or v <= 0 for v in universe):
        raise ValueError("variables must be positive integer IDs")
    permitted = set(universe)
    scores: Counter[tuple[int, int]] = Counter()
    events = 0
    for operation in operations:
        kind = operation.get("operation")
        if kind == "SWAP_ROWS":
            continue
        if kind != "ADD_ROW_XOR":
            raise ValueError("unsupported G5 operation kind")
        before = _support(operation.get("before"))
        source = _support(operation.get("source"))
        if not (before | source) <= permitted:
            raise ValueError("operation has variable outside declared universe")
        for left in before - source:
            for right in source - before:
                pair = (min(left, right), max(left, right))
                scores[pair] += 1
                events += 1
    pairs = tuple(combinations(universe, 2))
    ranked = tuple(sorted(
        pairs, key=lambda pair: (-scores[pair], pair)
    ))
    return {
        "status": "DIAGNOSTIC_ONLY",
        "ranked_pairs": ranked,
        "scores": {pair: scores[pair] for pair in pairs},
        "cross_merge_events": events,
    }
