"""Dynamic residual-component splitting *inside* DPLL.

Each recursive state is simplified by unit propagation. A graph of currently
remaining clauses is then traversed, and independently connected components
are solved as a conjunction. No oracle and no precomputed cut. Compare
standard frequency DPLL, frequency DPLL with splitting, and support hints
with splitting. This is known graph decomposition, not mathematical novelty.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from time import perf_counter

from scripts.benchmark_separator_decomposition import simplify, components
from scripts.experiment_inloop_support_hints import support_candidates
from scripts.benchmark_scaled_minisat_separator import scale_hidden_formula
from scripts.benchmark_incremental_minisat_separator import contradiction_variant
from scripts.experiment_autonomous_parity_separator import (
    _random_three_sat, _dense_bridge_negative,
)


def normalized_component_key(rows):
    """Variable-renaming-invariant signature for structurally identical CNFs.

    This simple sorted-variable relabeling is not a complete graph-isomorphism
    canonicalizer; it only finds a conservative subset of equivalent shapes.
    """
    variables = sorted({abs(lit) for row in rows for lit in row})
    renumber = {v: i + 1 for i, v in enumerate(variables)}
    return tuple(sorted(tuple(sorted(
        renumber[abs(lit)] if lit > 0 else -renumber[abs(lit)]
        for lit in row)) for row in rows))


def solve(rows, counters, *, split, hints=None, cache=None,
          event_driven=False, scan_allowed=True):
    counters["nodes"] += 1
    rows = tuple(tuple(row) for row in rows)
    while True:
        if not rows:
            return True
        if any(not row for row in rows):
            return False
        units = [row[0] for row in rows if len(row) == 1]
        if not units:
            break
        assigned = {}
        for literal in units:
            v, val = abs(literal), literal > 0
            if v in assigned and assigned[v] != val:
                return False
            assigned[v] = val
        reduced = simplify(rows, assigned)
        if reduced is None:
            return False
        rows = tuple(reduced)

    if split and scan_allowed:
        counters["component_scans"] += 1
        groups = components(rows)
        if len(groups) > 1:
            counters["split_events"] += 1
            counters["component_jobs"] += len(groups)
            # Exact AND decomposition. No requirement that the groups be SAT.
            for group in groups:
                if cache is None:
                    answer = solve(group, counters, split=split, hints=hints,
                                   event_driven=event_driven,
                                   scan_allowed=not event_driven)
                else:
                    signature = normalized_component_key(group)
                    if signature in cache:
                        counters["cache_hits"] += 1
                        answer = cache[signature]
                    else:
                        answer = solve(group, counters, split=split,
                                       hints=hints, cache=cache,
                                       event_driven=event_driven,
                                       scan_allowed=not event_driven)
                        cache[signature] = answer
                if not answer:
                    return False
            return True

    occurrences = Counter(abs(lit) for row in rows for lit in row)
    chosen = min(occurrences, key=lambda v: (
        -(hints or {}).get(v, 0), -occurrences[v], v))
    counters["decisions"] += 1
    if hints and hints.get(chosen, 0):
        counters["hinted_decisions"] += 1
    for val in (True, False):
        reduced = simplify(rows, {chosen: val})
        if reduced is not None and solve(reduced, counters,
                                         split=split, hints=hints, cache=cache,
                                         event_driven=event_driven,
                                         scan_allowed=(not event_driven or
                                                       bool(hints and hints.get(chosen, 0)))):
            return True
    return False


def run(formula, variant):
    rows = formula.to_clause_lists()
    split = variant != "frequency"
    use_cache = variant in ("support_split_cache", "support_split_event_cache")
    event_driven = variant == "support_split_event_cache"
    start = perf_counter()
    hints = support_candidates(rows) if variant in (
        "support_split", "support_split_cache", "support_split_event_cache") else None
    stats = {
        "nodes": 0, "decisions": 0, "hinted_decisions": 0,
        "component_scans": 0, "split_events": 0, "component_jobs": 0,
        "cache_hits": 0,
    }
    answer = solve(rows, stats, split=split, hints=hints,
                   cache={} if use_cache else None,
                   event_driven=event_driven, scan_allowed=not event_driven)
    return {
        "sat": answer, **stats,
        "elapsed_ms": round((perf_counter() - start) * 1000, 5),
    }


def benchmark(seed_count=8):
    cases = []
    for copies in (1, 2, 4, 8):
        for seed in range(seed_count):
            original = scale_hidden_formula(seed, copies)
            cases.append(("structured_sat", copies, seed, original))
            cases.append(("structured_unsat", copies, seed,
                          contradiction_variant(original)))
    for seed in range(seed_count):
        cases.append(("random_3sat", 0, seed, _random_three_sat(seed)))
        cases.append(("dense_bridge_negative", 0, seed,
                      _dense_bridge_negative(seed)))
    records = []
    for family, copies, seed, formula in cases:
        variants = {
            name: run(formula, name)
            for name in ("frequency", "frequency_split", "support_split",
                             "support_split_cache", "support_split_event_cache")
        }
        if len({item["sat"] for item in variants.values()}) != 1:
            raise AssertionError((family, copies, seed, "SAT disagreement"))
        records.append({"family": family, "copies": copies, "seed": seed,
                        "vars": formula.num_vars, **variants})
    return {
        "summary": {
            "total": len(records), "answers_agree": len(records),
            "frequency_split_node_wins": sum(
                r["frequency_split"]["nodes"] < r["frequency"]["nodes"]
                for r in records),
            "frequency_split_time_wins": sum(
                r["frequency_split"]["elapsed_ms"]
                < r["frequency"]["elapsed_ms"] for r in records),
            "support_over_split_node_wins": sum(
                r["support_split"]["nodes"]
                < r["frequency_split"]["nodes"] for r in records),
            "support_over_split_time_wins": sum(
                r["support_split"]["elapsed_ms"]
                < r["frequency_split"]["elapsed_ms"] for r in records),
            "cache_node_wins_over_support_split": sum(
                r["support_split_cache"]["nodes"]
                < r["support_split"]["nodes"] for r in records),
            "cache_time_wins_over_support_split": sum(
                r["support_split_cache"]["elapsed_ms"]
                < r["support_split"]["elapsed_ms"] for r in records),
            "cache_over_frequency_node_wins": sum(
                r["support_split_cache"]["nodes"] < r["frequency"]["nodes"]
                for r in records),
            "cache_over_frequency_time_wins": sum(
                r["support_split_cache"]["elapsed_ms"]
                < r["frequency"]["elapsed_ms"] for r in records),
            "total_frequency_ms": round(sum(
                r["frequency"]["elapsed_ms"] for r in records), 4),
            "total_cached_ms": round(sum(
                r["support_split_cache"]["elapsed_ms"] for r in records), 4),
            "total_cache_hits": sum(
                r["support_split_cache"]["cache_hits"] for r in records),
            "event_vs_cached_node_wins": sum(
                r["support_split_event_cache"]["nodes"]
                < r["support_split_cache"]["nodes"] for r in records),
            "event_vs_cached_time_wins": sum(
                r["support_split_event_cache"]["elapsed_ms"]
                < r["support_split_cache"]["elapsed_ms"] for r in records),
            "event_vs_frequency_time_wins": sum(
                r["support_split_event_cache"]["elapsed_ms"]
                < r["frequency"]["elapsed_ms"] for r in records),
            "event_total_ms": round(sum(
                r["support_split_event_cache"]["elapsed_ms"]
                for r in records), 4),
            "event_component_scans": sum(
                r["support_split_event_cache"]["component_scans"]
                for r in records),
            "cached_component_scans": sum(
                r["support_split_cache"]["component_scans"]
                for r in records),
            "total_split_events": sum(
                r["frequency_split"]["split_events"] for r in records),
            "novelty_established": False,
        },
        "by_scale": [{
            "family": family, "copies": copies,
            "frequency_nodes": sum(r["frequency"]["nodes"] for r in records
                                   if r["family"] == family
                                   and r["copies"] == copies),
            "split_nodes": sum(r["frequency_split"]["nodes"] for r in records
                               if r["family"] == family
                               and r["copies"] == copies),
            "support_split_nodes": sum(
                r["support_split"]["nodes"] for r in records
                if r["family"] == family and r["copies"] == copies),
            "cache_nodes": sum(r["support_split_cache"]["nodes"]
                               for r in records if r["family"] == family
                               and r["copies"] == copies),
            "cache_hits": sum(r["support_split_cache"]["cache_hits"]
                              for r in records if r["family"] == family
                              and r["copies"] == copies),
            "split_events": sum(r["frequency_split"]["split_events"]
                                for r in records if r["family"] == family
                                and r["copies"] == copies),
        } for family in ("structured_sat", "structured_unsat")
          for copies in (1, 2, 4, 8)],
        "records": records,
    }


def main():
    result = benchmark()
    path = Path("research/inloop_dynamic_split_results.json")
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))
    for item in result["by_scale"]:
        print(json.dumps(item, sort_keys=True))


if __name__ == "__main__":
    main()
