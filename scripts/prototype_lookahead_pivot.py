"""Fresh-seed falsification study of two-ply lookahead vs greedy elimination."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from time import perf_counter

from scripts.benchmark_operator_ood import timed_glucose
from witnora_core.experimental_operator_search import (
    bounded_elimination, independent_sat, structural_score,
)
from witnora_core.lookahead_pivot_prototype import two_ply_pivot
from witnora_core.ood_sat_families import larger_unseen_cases


def run(seeds=(613, 719), repeats=3):
    observations = []
    for seed in seeds:
        for family, case_id, source, expected in larger_unseen_cases(seed):
            source_truth = independent_sat(source)
            if expected is not None and source_truth["glucose3"] != expected:
                raise AssertionError("incorrect fresh family truth")
            truth, source_ms = timed_glucose(source, repeats)
            if truth != source_truth["glucose3"]:
                raise AssertionError("original SAT oracle conflict")
            start = perf_counter()
            greedy = bounded_elimination(bounded_elimination(source))
            greedy_prep_ms = (perf_counter() - start) * 1000
            start = perf_counter()
            lookahead = two_ply_pivot(source)
            lookahead_prep_ms = (perf_counter() - start) * 1000
            for strategy, transformed, prep_ms in (
                    ("greedy_two_steps", greedy, greedy_prep_ms),
                    ("speculative_two_ply", lookahead, lookahead_prep_ms)):
                oracle = independent_sat(transformed)
                candidate_truth, solve_ms = timed_glucose(transformed, repeats)
                if oracle != source_truth or candidate_truth != truth:
                    raise AssertionError(f"SAT mismatch: {case_id} {strategy}")
                observations.append({
                    "seed": seed, "family": family, "case_id": case_id,
                    "strategy": strategy,
                    "source_sha256": source.formula_hash,
                    "candidate_sha256": transformed.formula_hash,
                    "source_variables": source.num_vars,
                    "candidate_variables": transformed.num_vars,
                    "source_clauses": source.num_clauses,
                    "candidate_clauses": transformed.num_clauses,
                    "satisfiable": int(truth),
                    "structural_gain": round(structural_score(source, transformed), 6),
                    "source_solve_median_ms": round(source_ms, 6),
                    "preprocess_ms": round(prep_ms, 6),
                    "candidate_solve_median_ms": round(solve_ms, 6),
                    "total_ms": round(prep_ms + solve_ms, 6),
                    "independent_solver_agreement": True,
                    "novel_inference_rule": False,
                    "lean_verified": False,
                    "promoted": False,
                })
    return observations


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("lookahead-pivot-study.csv"))
    parser.add_argument("--seeds", type=int, nargs="+", default=[613, 719])
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    records = run(args.seeds, args.repeats)
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    pairs = {(row["seed"], row["case_id"]): row for row in records
             if row["strategy"] == "greedy_two_steps"}
    wins = []
    runtime_wins = []
    for row in records:
        if row["strategy"] != "speculative_two_ply":
            continue
        baseline = pairs[(row["seed"], row["case_id"])]
        wins.append(row["structural_gain"] > baseline["structural_gain"])
        runtime_wins.append(row["total_ms"] < baseline["total_ms"])
    print({
        "cases": len(wins),
        "structural_wins_over_greedy": sum(wins),
        "end_to_end_time_wins_over_greedy": sum(runtime_wins),
        "SAT_oracles_agree": True,
        "new_inference_rule_proven": False,
        "output": str(args.output),
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
