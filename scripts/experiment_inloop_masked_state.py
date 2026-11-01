"""Persist residual clause-support masks through DPLL branching.

Each clause carries an integer bitset updated when assignments remove
literals. Component detection uses these masks directly (no reconstructed
variable adjacency graph). Exact normalized component keys remain the
authority for cache reuse. Exploratory synthetic and OOD benchmark.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from statistics import median
from pysat.solvers import Minisat22
from time import perf_counter

from scripts.experiment_inloop_dynamic_split import run as reference_run
from scripts.experiment_inloop_dynamic_split import normalized_component_key
from scripts.experiment_inloop_support_hints import support_candidates
from scripts.experiment_event_cached_ood import (
    random_three_sat, disconnected_three_sat, mixed_random_parities,
)
from scripts.benchmark_scaled_minisat_separator import scale_hidden_formula


def clauses_with_masks(rows):
    return tuple((tuple(row), sum(1 << abs(lit) for lit in row))
                 for row in rows)


def simplify_masked(state, assignment):
    assigned = sum(1 << v for v in assignment)
    result = []
    for row, mask in state:
        if mask & assigned == 0:
            result.append((row, mask))
            continue
        if any(((lit > 0) == assignment[abs(lit)])
               for lit in row if abs(lit) in assignment):
            continue
        reduced = tuple(lit for lit in row if abs(lit) not in assignment)
        if not reduced:
            return None
        result.append((reduced, mask & ~assigned))
    return tuple(result)


def components_masked(state):
    """Exact connected clause components via expanding overlapping masks."""
    remaining = list(state)
    groups = []
    while remaining:
        first = remaining.pop()
        group = [first]
        reach = first[1]
        changed = True
        while changed:
            changed = False
            kept = []
            for item in remaining:
                if item[1] & reach:
                    group.append(item)
                    reach |= item[1]
                    changed = True
                else:
                    kept.append(item)
            remaining = kept
        groups.append(tuple(group))
    return groups


def solve(state, hints, counters, cache, hint_depth=0):
    counters["nodes"] += 1
    while True:
        if not state:
            return True
        if any(not row for row, _ in state):
            return False
        units = [row[0] for row, _ in state if len(row) == 1]
        if not units:
            break
        assignment = {}
        for lit in units:
            v, value = abs(lit), lit > 0
            if v in assignment and assignment[v] != value:
                return False
            assignment[v] = value
        reduced = simplify_masked(state, assignment)
        if reduced is None:
            return False
        state = reduced

    if hint_depth >= 2:
        counters["component_scans"] += 1
        groups = components_masked(state)
        if len(groups) > 1:
            counters["split_events"] += 1
            for group in groups:
                rows = [row for row, _ in group]
                signature = normalized_component_key(rows)
                if signature in cache:
                    counters["cache_hits"] += 1
                    answer = cache[signature]
                else:
                    answer = solve(group, hints, counters, cache, 0)
                    cache[signature] = answer
                if not answer:
                    return False
            return True

    occurrences = Counter(abs(lit) for row, _ in state for lit in row)
    chosen = min(occurrences, key=lambda v: (-hints.get(v, 0),
                                             -occurrences[v], v))
    counters["decisions"] += 1
    for value in (True, False):
        reduced = simplify_masked(state, {chosen: value})
        if reduced is not None and solve(
            reduced, hints, counters, cache,
            hint_depth + int(bool(hints.get(chosen, 0)))
            if hints.get(chosen, 0) else 0,
        ):
            return True
    return False


def run_masked(formula):
    rows = formula.to_clause_lists()
    start = perf_counter()
    hints = support_candidates(rows)
    counters = {"nodes": 0, "decisions": 0, "component_scans": 0,
                "split_events": 0, "cache_hits": 0}
    sat = solve(clauses_with_masks(rows), hints, counters, {})
    return {"sat": sat, **counters,
            "elapsed_ms": round((perf_counter() - start) * 1000, 5)}


def benchmark(seed_count=8, repeats=5):
    records = []
    families = [
        ("hidden", lambda s: scale_hidden_formula(s, 8)),
        ("random_3sat", random_three_sat),
        ("disconnected_3sat", disconnected_three_sat),
        ("mixed_parity", mixed_random_parities),
        ("bridged_parity", lambda s: mixed_random_parities(s, bridge=True)),
    ]
    for family, generator in families:
        for seed in range(seed_count):
            formula = generator(seed)
            old = [reference_run(formula, "support_split_event2_cache")
                   for _ in range(repeats)]
            new = [run_masked(formula) for _ in range(repeats)]
            with Minisat22(bootstrap_with=formula.to_clause_lists()) as oracle:
                expected = oracle.solve()
            if len({r["sat"] for r in old + new} | {expected}) != 1:
                raise AssertionError((family, seed, "SAT disagreement"))
            records.append({
                "family": family, "seed": seed,
                "reference_nodes": old[0]["nodes"],
                "masked_nodes": new[0]["nodes"],
                "reference_ms": median(r["elapsed_ms"] for r in old),
                "masked_ms": median(r["elapsed_ms"] for r in new),
                "masked_cache_hits": new[0]["cache_hits"],
                "masked_component_scans": new[0]["component_scans"],
            })
    return {
        "summary": {
            "total": len(records), "answers_agree": len(records),
            "masked_time_wins": sum(r["masked_ms"] < r["reference_ms"]
                                    for r in records),
            "masked_node_wins": sum(r["masked_nodes"] < r["reference_nodes"]
                                    for r in records),
            "reference_total_ms": round(sum(r["reference_ms"] for r in records), 4),
            "masked_total_ms": round(sum(r["masked_ms"] for r in records), 4),
            "masked_cache_hits": sum(r["masked_cache_hits"] for r in records),
            "novelty_established": False,
        },
        "by_family": [{
            "family": family,
            "reference_ms": round(sum(r["reference_ms"] for r in records
                                      if r["family"] == family), 5),
            "masked_ms": round(sum(r["masked_ms"] for r in records
                                   if r["family"] == family), 5),
            "wins": sum(r["masked_ms"] < r["reference_ms"] for r in records
                        if r["family"] == family),
            "cache_hits": sum(r["masked_cache_hits"] for r in records
                              if r["family"] == family),
        } for family, _ in families],
        "records": records,
    }


def main():
    result = benchmark()
    Path("research/inloop_masked_state_results.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))
    for family in result["by_family"]:
        print(json.dumps(family, sort_keys=True))


if __name__ == "__main__":
    main()
