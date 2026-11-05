"""Indexed unit-conflict witnesses for an existing RUP certificate.

This is a faster *untrusted witness producer*: it builds literal occurrence
lists for each RUP addition and updates unsatisfied-clause counters incrementally
instead of scanning every clause after every derived unit. Its units are
independently checked by the existing Lean GeneralRUP kernel and the native
reference replay. It does not change the soundness theorem.

The canonical-clause convention is enforced by the calling DRUP importer.
"""
from __future__ import annotations

from collections import defaultdict, deque


def indexed_unit_conflict_witness(
    database: list[tuple[int, ...]],
    clause: tuple[int, ...],
    *,
    max_units: int = 100000,
    backend: str = "python",
) -> tuple[int, ...] | None:
    if max_units < 0:
        raise ValueError("max_units must be nonnegative")
    if backend == "rust":
        from witnora_ve import indexed_rup_witness_native
        result = indexed_rup_witness_native(
            [list(row) for row in database], list(clause), max_units)
        return None if result is None else tuple(result)
    if backend != "python":
        raise ValueError("unknown indexed RUP witness backend")
    assumptions = {-lit for lit in clause}
    satisfied: list[bool] = []
    remaining: list[int] = []
    occurrence: dict[int, list[int]] = defaultdict(list)
    ready: deque[int] = deque()
    for i, row in enumerate(database):
        # The caller passes duplicate-cancelled canonical source and DRUP rows.
        # Deduplication here additionally preserves behavior for arbitrary
        # callers: a repeated identical literal does not create a second unit.
        unique = tuple(dict.fromkeys(row))
        for lit in unique:
            occurrence[lit].append(i)
        sat = any(lit in assumptions for lit in unique)
        count = sum(-lit not in assumptions for lit in unique)
        satisfied.append(sat)
        remaining.append(count)
        if not sat and count == 0:
            return ()
        if not sat and count == 1:
            ready.append(i)
    units: list[int] = []
    while ready:
        i = ready.popleft()
        if satisfied[i] or remaining[i] != 1:
            continue
        row = database[i]
        candidates = [lit for lit in dict.fromkeys(row) if -lit not in assumptions]
        if len(candidates) != 1:
            return None  # stale/corrupt counter: fail closed
        forced = candidates[0]
        if forced in assumptions:
            continue  # already satisfied; defensive against duplicate work
        if -forced in assumptions or len(units) >= max_units:
            return None
        assumptions.add(forced)
        units.append(forced)
        for j in occurrence.get(forced, ()):
            satisfied[j] = True
        for j in occurrence.get(-forced, ()):
            if satisfied[j]:
                continue
            remaining[j] -= 1
            if remaining[j] == 0:
                return tuple(units)
            if remaining[j] == 1:
                ready.append(j)
    return None
