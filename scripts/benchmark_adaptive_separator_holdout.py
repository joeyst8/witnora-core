"""Train-only size gate for incremental separator guidance; strict held-out test.

The gate receives only structural features and a discovered cut, never SAT
status or benchmark case labels. Timings train on seeds 0..7 and are
evaluated on disjoint seeds 8..23. Repeated solvers are freshly initialized.
"""
from __future__ import annotations

import json
from pathlib import Path
from statistics import median
from time import perf_counter

from witnora_core.autonomous_parity_separator import discover_repaired_separator
from scripts.benchmark_scaled_minisat_separator import scale_hidden_formula
from scripts.benchmark_incremental_minisat_separator import (
    contradiction_variant, fresh_solver_answer, incremental_cut_answer,
)


def timed(callback, repeats):
    times = []
    answer = None
    for _ in range(repeats):
        start = perf_counter()
        next_answer = callback()
        times.append((perf_counter() - start) * 1000)
        if answer is None:
            answer = next_answer
        elif next_answer != answer:
            raise AssertionError("solver result varied")
    return answer, median(times)


def cases(seeds, repeats=11):
    records = []
    for seed in seeds:
        for copies in (1, 2, 4, 8):
            original = scale_hidden_formula(seed, copies)
            for variant, formula in (
                ("original", original),
                ("parity_contradiction", contradiction_variant(original)),
            ):
                rows = formula.to_clause_lists()
                base_sat, base_ms = timed(
                    lambda: fresh_solver_answer(rows), repeats)
                started = perf_counter()
                result = discover_repaired_separator(formula)
                detect_ms = (perf_counter() - started) * 1000
                cut = result["cut"] if result["status"] == "FOUND" else None
                if cut is None:
                    guided_sat, guided_ms = base_sat, None
                else:
                    guided_sat, guided_ms = timed(
                        lambda: incremental_cut_answer(rows, cut), repeats)
                if guided_sat != base_sat:
                    raise AssertionError(("wrong answer", seed, copies, variant))
                records.append({
                    "seed": seed, "copies": copies, "variant": variant,
                    "vars": formula.num_vars, "clauses": formula.num_clauses,
                    "sat_for_audit_only": base_sat,
                    "cut_size": len(cut) if cut is not None else None,
                    "base_ms": base_ms, "guided_ms": guided_ms,
                    "discovery_ms": detect_ms,
                })
    return records


def use_guidance(record, min_vars):
    return (record["cut_size"] is not None
            and record["vars"] >= min_vars)


def total_time(records, min_vars, include_discovery=False):
    return sum(
        (record["guided_ms"] if use_guidance(record, min_vars)
         else record["base_ms"])
        + (record["discovery_ms"] if include_discovery
           and record["vars"] >= min_vars else 0)
        for record in records)


def summarize(records, min_vars):
    base = total_time(records, 10**9)
    guided = total_time(records, min_vars)
    first_use = total_time(records, min_vars, include_discovery=True)
    return {
        "cases": len(records), "baseline_total_ms": round(base, 4),
        "policy_cached_total_ms": round(guided, 4),
        "policy_including_detection_total_ms": round(first_use, 4),
        "cached_ratio_vs_baseline": round(guided / base, 4),
        "first_use_ratio_vs_baseline": round(first_use / base, 4),
        "guided_count": sum(use_guidance(r, min_vars) for r in records),
        "answers_agree": len(records),
    }


def benchmark(train_seeds=range(8), test_seeds=range(8, 24), repeats=11):
    if set(train_seeds) & set(test_seeds):
        raise ValueError("train/test seeds overlap")
    train = cases(train_seeds, repeats)
    test = cases(test_seeds, repeats)
    options = (0, 10, 20, 30, 40, 60, 100, 10**9)
    chosen = min(options, key=lambda cutoff: (
        total_time(train, cutoff), cutoff))
    return {
        "summary": {
            "chosen_min_vars": chosen,
            "train": summarize(train, chosen),
            "held_out": summarize(test, chosen),
            "always_guide_held_out": summarize(test, 0),
            "never_guide_held_out": summarize(test, 10**9),
            "seeds_disjoint": True,
            "policy_uses_sat_labels": False,
            "discovery_not_amortized_for_first_use": True,
            "synthetic_family_only": True,
            "novelty_established": False,
        },
        "train_records": train,
        "held_out_records": test,
        "training_cutoff_scores": [
            {"min_vars": cutoff,
             "cached_total_ms": round(total_time(train, cutoff), 5)}
            for cutoff in options
        ],
    }


def main():
    result = benchmark()
    path = Path("research/adaptive_separator_holdout_benchmark.json")
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
