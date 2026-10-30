"""Predeclared scaling study of direct SAT against full conditioned pipeline."""
from __future__ import annotations

import csv
from pathlib import Path
from statistics import median
from time import perf_counter

from pysat.solvers import Glucose3
from witnora_core.experimental_operator_search import independent_sat
from witnora_core.separator_conditioned_solve import solve_conditioned
from witnora_core.separator_scaling_families import make_scaling_case


def direct(formula):
    with Glucose3(bootstrap_with=formula.to_clause_lists()) as solver:
        return bool(solver.solve())


def time_call(fn):
    start = perf_counter()
    result = fn()
    return result, (perf_counter() - start) * 1000


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("separator-scaling.csv"))
    args = parser.parse_args()
    rows = []
    for width in (2, 3):
        for blocks in (2, 4, 8, 16, 32):
            source, meta = make_scaling_case(blocks, width)
            truth = independent_sat(source)
            direct_times, conditioned_times = [], []
            modes = set()
            for repeat in range(5):
                # Alternate execution order to reduce systematic warm-cache bias.
                if repeat % 2:
                    conditioned_result, conditional_ms = time_call(
                        lambda: solve_conditioned(source))
                    direct_truth, direct_ms = time_call(lambda: direct(source))
                else:
                    direct_truth, direct_ms = time_call(lambda: direct(source))
                    conditioned_result, conditional_ms = time_call(
                        lambda: solve_conditioned(source))
                if (direct_truth != truth["glucose3"]
                        or conditioned_result["satisfiable"] != truth["glucose3"]):
                    raise AssertionError("scaling SAT truth disagreement")
                modes.add(conditioned_result["mode"])
                direct_times.append(direct_ms)
                conditioned_times.append(conditional_ms)
            if modes != {"conditioned"}:
                raise AssertionError("planned separator not used")
            direct_median = median(direct_times)
            conditional_median = median(conditioned_times)
            rows.append({
                "width": width, "blocks_per_side": blocks,
                "source_sha256": source.formula_hash,
                "variables": source.num_vars,
                "clauses": source.num_clauses,
                "equations": meta["parity_equations"],
                "direct_median_ms": round(direct_median, 6),
                "conditioned_median_ms": round(conditional_median, 6),
                "speed_ratio_direct_over_conditioned": round(
                    direct_median / conditional_median, 6) if conditional_median else 0,
                "conditioned_faster": conditional_median < direct_median,
                "truth_agrees": True, "lean_verified": False,
                "promoted": False,
            })
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print({"cases": len(rows),
           "conditioned_runtime_wins": sum(r["conditioned_faster"] for r in rows),
           "largest_case": max(r["clauses"] for r in rows),
           "all_truths_agree": True, "trusted": False})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
