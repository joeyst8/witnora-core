"""Repeated-query incremental MiniSat study with cheap structural pre-screen.

One persistent solver per arm. The pre-screen reads only variable/clause
counts and maximum clause width; it does NOT use the answer or hidden
separator metadata. SAT queries are held constant across arms.
"""
from __future__ import annotations

import json
from pathlib import Path
from random import Random
from time import perf_counter

from pysat.solvers import Minisat22

from witnora_core.autonomous_parity_separator import discover_repaired_separator
from scripts.benchmark_scaled_minisat_separator import scale_hidden_formula
from scripts.experiment_autonomous_parity_separator import _random_three_sat


def cheap_screen(formula):
    """Linear-in-input prefilter, tuned for large wide-clause formulas only."""
    return (formula.num_vars >= 40
            and any(len(row) >= 4 for row in formula.clauses))


def queries(formula, seed, count):
    rng = Random(19000 + seed)
    variables = tuple(formula.variables)
    result = []
    for _ in range(count):
        chosen = rng.sample(variables, min(3, len(variables)))
        result.append([v if rng.getrandbits(1) else -v for v in chosen])
    return result


def run_queries(rows, batches, cut=None):
    answers = []
    started = perf_counter()
    with Minisat22(bootstrap_with=rows) as solver:
        for query in batches:
            if cut is None:
                answers.append(solver.solve(assumptions=query))
                continue
            sat = False
            for mask in range(1 << len(cut)):
                assignment = [v if mask & (1 << i) else -v
                              for i, v in enumerate(cut)]
                if solver.solve(assumptions=query + assignment):
                    sat = True
                    break
            answers.append(sat)
    return answers, (perf_counter() - started) * 1000


def benchmark(seed_count=8, workloads=(1, 10, 100, 1000)):
    records = []
    for copies in (4, 8):
        for seed in range(seed_count):
            formula = scale_hidden_formula(seed, copies)
            for query_count in workloads:
                batches = queries(formula, seed, query_count)
                rows = formula.to_clause_lists()
                baseline, plain_ms = run_queries(rows, batches)
                started = perf_counter()
                screen = cheap_screen(formula)
                screen_ms = (perf_counter() - started) * 1000
                cut = None
                detection_ms = 0.0
                if screen:
                    started = perf_counter()
                    result = discover_repaired_separator(formula)
                    detection_ms = (perf_counter() - started) * 1000
                    if result["status"] == "FOUND":
                        cut = result["cut"]
                if cut is None:
                    assisted, guided_ms = run_queries(rows, batches)
                else:
                    assisted, guided_ms = run_queries(rows, batches, cut)
                if baseline != assisted:
                    raise AssertionError(("query answer mismatch", copies, seed,
                                          query_count))
                records.append({
                    "copies": copies, "seed": seed, "queries": query_count,
                    "screen": screen, "cut": cut,
                    "baseline_ms": round(plain_ms, 5),
                    "guided_solver_ms": round(guided_ms, 5),
                    "discovery_ms": round(detection_ms, 5),
                    "screen_ms": round(screen_ms, 5),
                    "guided_total_ms": round(
                        guided_ms + detection_ms + screen_ms, 5),
                    "query_answers_agree": len(batches),
                })
    # Unstructured null controls: measure screen selectivity only.
    nulls = [_random_three_sat(seed) for seed in range(seed_count)]
    return {
        "summary": {
            "total_workloads": len(records),
            "all_query_answers_agree": True,
            "random_3sat_screen_passes": sum(cheap_screen(f) for f in nulls),
            "selected_workloads": sum(r["cut"] is not None for r in records),
            "cached_wins": sum(
                r["guided_solver_ms"] < r["baseline_ms"]
                for r in records if r["cut"] is not None),
            "end_to_end_wins": sum(
                r["guided_total_ms"] < r["baseline_ms"]
                for r in records),
            "selected_end_to_end_wins": sum(
                r["guided_total_ms"] < r["baseline_ms"]
                for r in records if r["cut"] is not None),
            "novelty_established": False,
            "synthetic_benchmark": True,
        },
        "by_workload": [{
            "copies": copies, "queries": query_count,
            "baseline_total_ms": round(sum(
                r["baseline_ms"] for r in records
                if r["copies"] == copies and r["queries"] == query_count), 4),
            "guided_total_ms": round(sum(
                r["guided_total_ms"] for r in records
                if r["copies"] == copies and r["queries"] == query_count), 4),
        } for copies in (4, 8) for query_count in workloads],
        "records": records,
    }


def main():
    result = benchmark()
    path = Path("research/repeated_query_separator_benchmark.json")
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))
    for group in result["by_workload"]:
        print(json.dumps(group, sort_keys=True))


if __name__ == "__main__":
    main()
