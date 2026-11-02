"""Matched-core, source-bound XOR propagation ablation.

The exact same recursive DPLL core and branching heuristic receives either
no parity rows, recovered original rows, or original + pairwise deductions.
Times include extraction and deduction per solve (not formula construction).
"""
from __future__ import annotations

from collections import Counter
from statistics import median
from time import perf_counter

from pysat.solvers import Minisat22

from scripts.experiment_cross_support_propagation import (
    derive_small_rows, extract_rows, make_case, solve,
)
from scripts.experiment_event_cached_ood import random_three_sat, mixed_random_parities


def timed_solve(formula, mode):
    start = perf_counter()
    rows = ()
    if mode != "none":
        rows = extract_rows(formula)
        if mode == "derived":
            rows = derive_small_rows(rows)
    counters = Counter()
    sat = solve(tuple(map(tuple, formula.to_clause_lists())), rows, counters)
    return {"sat": sat, "elapsed_ms": (perf_counter() - start) * 1000,
            "rows": len(rows), **counters}


def benchmark(seeds=12, repeats=7):
    if seeds < 1 or repeats < 1:
        raise ValueError("seeds and repeats must be positive")
    records = []
    modes = ("none", "source", "derived")
    cases = []
    for n in (16, 32):
        for seed in range(seeds):
            for kind in ("conflict", "imply", "sat", "random"):
                cases.append((f"cross_{kind}", n, seed, make_case(n, seed, kind)))
    for seed in range(seeds):
        cases.extend([
            ("ood_3sat", 0, seed, random_three_sat(seed)),
            ("ood_parity", 0, seed, mixed_random_parities(seed)),
        ])
    for family, n, seed, formula in cases:
        with Minisat22(bootstrap_with=formula.to_clause_lists()) as oracle:
            expected = oracle.solve()
        trials = {mode: [] for mode in modes}
        for rep in range(repeats):
            # Rotate order to avoid always charging startup/caches to one mode.
            for mode in modes[rep % 3:] + modes[:rep % 3]:
                data = timed_solve(formula, mode)
                if data["sat"] != expected:
                    raise AssertionError((family, seed, mode, expected, data))
                trials[mode].append(data)
        native_times = []
        for _ in range(repeats):
            start = perf_counter()
            with Minisat22(bootstrap_with=formula.to_clause_lists()) as native:
                native_result = native.solve()
            if native_result != expected:
                raise AssertionError((family, seed, "native_minisat_disagree"))
            native_times.append((perf_counter() - start) * 1000)
        record = {"family": family, "n": n, "seed": seed,
                  "sat": expected, "source_rows": len(extract_rows(formula)),
                  "minisat_ms": median(native_times)}
        for mode in modes:
            record[mode + "_ms"] = median(r["elapsed_ms"] for r in trials[mode])
            record[mode + "_nodes"] = trials[mode][0].get("nodes", 0)
            record[mode + "_decisions"] = trials[mode][0].get("decisions", 0)
            record[mode + "_affine_implied"] = trials[mode][0].get("affine_implied", 0)
            record[mode + "_affine_conflicts"] = trials[mode][0].get("affine_conflicts", 0)
        records.append(record)
    return {"summary": {
        "cases": len(records), "all_answers_agree_minisat": True,
        "source_rows_cases": sum(r["source_rows"] > 0 for r in records),
        "derived_vs_none_node_wins": sum(r["derived_nodes"] < r["none_nodes"] for r in records),
        "derived_vs_source_node_wins": sum(r["derived_nodes"] < r["source_nodes"] for r in records),
        "derived_vs_source_decision_wins": sum(r["derived_decisions"] < r["source_decisions"] for r in records),
        "derived_vs_source_time_wins": sum(r["derived_ms"] < r["source_ms"] for r in records),
        "source_vs_none_time_wins": sum(r["source_ms"] < r["none_ms"] for r in records),
        "derived_total_implied": sum(r["derived_affine_implied"] for r in records),
        "source_total_implied": sum(r["source_affine_implied"] for r in records),
        "minisat_total_ms": round(sum(r["minisat_ms"] for r in records), 4),
        **{mode + "_total_ms": round(sum(r[mode + "_ms"] for r in records), 4)
           for mode in modes},
    }, "by_family": [{"family": family,
                      "count": sum(r["family"] == family for r in records),
                      **{mode + "_total_ms": round(sum(r[mode + "_ms"] for r in records
                                                        if r["family"] == family), 4)
                         for mode in modes},
                      "minisat_total_ms": round(sum(r["minisat_ms"] for r in records
                                                     if r["family"] == family), 4),
                      "derived_node_wins_vs_source": sum(r["derived_nodes"] < r["source_nodes"]
                                                         for r in records if r["family"] == family)}
                     for family in sorted({r["family"] for r in records})],
            "records": records}


if __name__ == "__main__":
    import json
    result = benchmark()
    print(json.dumps(result["summary"], indent=2))
    print(json.dumps(result["by_family"], indent=2))
