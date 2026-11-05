"""Fresh-seed four-strategy challenge with separately measured preprocessing."""
from __future__ import annotations

import csv
from pathlib import Path
from time import perf_counter

from scripts.benchmark_operator_ood import timed_glucose
from witnora_core.adaptive_lookahead_prototype import adaptive_pivot
from witnora_core.experimental_operator_search import bounded_elimination, independent_sat, structural_score
from witnora_core.lookahead_pivot_prototype import two_ply_pivot
from witnora_core.ood_sat_families import larger_unseen_cases
from witnora_core.selective_lookahead_prototype import selective_pivot


def run(seeds=(1061, 1201), repeats=3):
    rows = []
    for seed in seeds:
        for family, case_id, source, expected in larger_unseen_cases(seed):
            truth = independent_sat(source)
            if expected is not None and truth["glucose3"] != expected:
                raise AssertionError("source truth mismatch")
            for name, operator in (
                ("greedy", lambda: bounded_elimination(bounded_elimination(source))),
                ("fixed_two_ply", lambda: two_ply_pivot(source)),
                ("adaptive", lambda: adaptive_pivot(source)[0]),
                ("selective", lambda: selective_pivot(source)[0]),
            ):
                start = perf_counter()
                result = operator()
                prep_ms = (perf_counter() - start) * 1000
                if independent_sat(result) != truth:
                    raise AssertionError(f"oracle mismatch {case_id} {name}")
                solved, solve_ms = timed_glucose(result, repeats)
                if solved != truth["glucose3"]:
                    raise AssertionError(f"timed oracle mismatch {case_id} {name}")
                rows.append({
                    "seed": seed, "family": family, "case_id": case_id,
                    "strategy": name, "source_sha256": source.formula_hash,
                    "candidate_sha256": result.formula_hash,
                    "structural_gain": round(structural_score(source, result), 6),
                    "prep_ms": round(prep_ms, 6),
                    "solve_median_ms": round(solve_ms, 6),
                    "total_ms": round(prep_ms + solve_ms, 6),
                    "independent_solver_agreement": True,
                    "lean_verified": False, "promoted": False,
                })
    return rows


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("selective-lookahead.csv"))
    args = parser.parse_args()
    rows = run()
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    pairs = {}
    for row in rows:
        pairs.setdefault((row["seed"], row["case_id"]), {})[row["strategy"]] = row
    for baseline in ("greedy", "fixed_two_ply", "adaptive"):
        print({f"selective_structural_wins_vs_{baseline}": sum(
            p["selective"]["structural_gain"] > p[baseline]["structural_gain"]
            for p in pairs.values()),
            f"selective_total_time_wins_vs_{baseline}": sum(
                p["selective"]["total_ms"] < p[baseline]["total_ms"]
                for p in pairs.values()), "cases": len(pairs)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
