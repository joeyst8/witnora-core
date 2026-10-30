"""Cold/warm cache timing, direct baseline, and exact-screen fallback."""
from __future__ import annotations

import csv
from pathlib import Path
from statistics import median
from time import perf_counter

from pysat.solvers import Glucose3
from witnora_core.experimental_operator_search import independent_sat
from witnora_core.hard_separator_families import make_hard_separator_case
from witnora_core.incremental_separator import (
    cached_full_cut, possible_two_xor_patterns, solve_incremental,
)
from witnora_core.ood_sat_families import larger_unseen_cases


def direct(formula):
    with Glucose3(bootstrap_with=formula.to_clause_lists()) as solver:
        return bool(solver.solve())


def timed(call):
    start = perf_counter()
    result = call()
    return result, (perf_counter() - start) * 1000


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("incremental-separator.csv"))
    args = parser.parse_args()
    cases = []
    for width in (2, 3):
        for blocks in (2, 4, 8):
            f, _ = make_hard_separator_case(blocks, 26, width, 3023)
            cases.append(("planted_core", f"w{width}_blocks{blocks}", f))
    for family, case_id, f, _ in larger_unseen_cases(2593):
        cases.append((family, case_id, f))
    rows = []
    for family, case_id, formula in cases:
        truth = independent_sat(formula)
        direct_samples, cold_samples, warm_samples = [], [], []
        for _ in range(3):
            direct_truth, direct_ms = timed(lambda: direct(formula))
            cached_full_cut.cache_clear()
            cold_result, cold_ms = timed(lambda: solve_incremental(formula))
            warm_result, warm_ms = timed(lambda: solve_incremental(formula))
            if not (direct_truth == cold_result["satisfiable"]
                    == warm_result["satisfiable"] == truth["glucose3"]):
                raise AssertionError("cache changed SAT truth")
            direct_samples.append(direct_ms)
            cold_samples.append(cold_ms)
            warm_samples.append(warm_ms)
        rows.append({
            "family": family, "case_id": case_id,
            "source_sha256": formula.formula_hash,
            "screen_positive": possible_two_xor_patterns(formula),
            "mode": warm_result["mode"],
            "direct_median_ms": round(median(direct_samples), 6),
            "cold_median_ms": round(median(cold_samples), 6),
            "warm_median_ms": round(median(warm_samples), 6),
            "cold_faster": median(cold_samples) < median(direct_samples),
            "warm_faster": median(warm_samples) < median(direct_samples),
            "truth_agrees": True, "lean_verified": False, "promoted": False,
        })
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print({"cases": len(rows),
           "cold_runtime_wins": sum(r["cold_faster"] for r in rows),
           "warm_runtime_wins": sum(r["warm_faster"] for r in rows),
           "screen_negative_cases": sum(not r["screen_positive"] for r in rows),
           "median_direct_ms": round(median(r["direct_median_ms"] for r in rows), 4),
           "median_cold_ms": round(median(r["cold_median_ms"] for r in rows), 4),
           "median_warm_ms": round(median(r["warm_median_ms"] for r in rows), 4),
           "all_truths_agree": True, "trusted": False})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
