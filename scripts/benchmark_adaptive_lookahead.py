"""Falsify budgeted adaptive lookahead on unseen OOD SAT cases."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from time import perf_counter

from scripts.benchmark_operator_ood import timed_glucose
from witnora_core.adaptive_lookahead_prototype import adaptive_pivot
from witnora_core.experimental_operator_search import bounded_elimination, independent_sat, structural_score
from witnora_core.lookahead_pivot_prototype import two_ply_pivot
from witnora_core.ood_sat_families import larger_unseen_cases


def run(seeds=(823, 941), repeats=3):
    rows = []
    for seed in seeds:
        for family, case_id, source, expected in larger_unseen_cases(seed):
            truth = independent_sat(source)
            if expected is not None and truth["glucose3"] != expected:
                raise AssertionError("source truth mismatch")
            for name, method in (
                ("greedy", lambda: bounded_elimination(bounded_elimination(source))),
                ("two_ply", lambda: two_ply_pivot(source)),
                ("adaptive", lambda: adaptive_pivot(source)[0]),
            ):
                start = perf_counter()
                candidate = method()
                prep_ms = (perf_counter() - start) * 1000
                if independent_sat(candidate) != truth:
                    raise AssertionError(f"SAT mismatch: {case_id} {name}")
                solved, solve_ms = timed_glucose(candidate, repeats)
                if solved != truth["glucose3"]:
                    raise AssertionError(f"timing oracle conflict: {case_id} {name}")
                rows.append({
                    "seed": seed, "family": family, "case_id": case_id,
                    "strategy": name, "source_sha256": source.formula_hash,
                    "candidate_sha256": candidate.formula_hash,
                    "structural_gain": round(structural_score(source, candidate), 6),
                    "preprocess_ms": round(prep_ms, 6),
                    "solve_median_ms": round(solve_ms, 6),
                    "total_ms": round(prep_ms + solve_ms, 6),
                    "independent_solver_agreement": True,
                    "lean_verified": False, "novelty_verified": False, "promoted": False,
                })
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("adaptive-lookahead.csv"))
    args = parser.parse_args()
    rows = run()
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    grouped = {}
    for row in rows:
        grouped.setdefault((row["seed"], row["case_id"]), {})[row["strategy"]] = row
    for comparator in ("greedy", "two_ply"):
        print({f"structural_wins_over_{comparator}": sum(
            pair["adaptive"]["structural_gain"] > pair[comparator]["structural_gain"]
            for pair in grouped.values()),
            f"total_time_wins_over_{comparator}": sum(
                pair["adaptive"]["total_ms"] < pair[comparator]["total_ms"]
                for pair in grouped.values()), "cases": len(grouped)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
