"""Break down structural discovery versus component SAT cost on hard-ish cores."""
from __future__ import annotations

import csv
from itertools import product
from pathlib import Path
from statistics import median
from time import perf_counter

from pysat.solvers import Glucose3
from witnora_core.experimental_operator_search import independent_sat
from witnora_core.hard_separator_families import make_hard_separator_case
from witnora_core.multicut_parity_separator import bounded_parity_separators
from witnora_core.separator_conditioned_solve import (
    primal_components, restrict_formula, split_residual,
)


def solve(formula):
    with Glucose3(bootstrap_with=formula.to_clause_lists()) as solver:
        return bool(solver.solve())


def conditioned_timed(formula):
    start = perf_counter()
    candidates = bounded_parity_separators(formula)["candidate_cuts"]
    cut = next((tuple(row["variables"]) for row in candidates
                if len(primal_components(formula, row["variables"]))
                > len(primal_components(formula))), None)
    detection_ms = (perf_counter() - start) * 1000
    if cut is None:
        raise AssertionError("planned complete separator not detected")
    component_ms = 0.0
    assignments = 0
    calls = 0
    result = False
    for values in product((False, True), repeat=len(cut)):
        assignments += 1
        residual = restrict_formula(formula, dict(zip(cut, values)))
        if residual.contains_empty_clause:
            continue
        all_sat = True
        for component in split_residual(residual):
            before = perf_counter()
            truth = solve(component)
            component_ms += (perf_counter() - before) * 1000
            calls += 1
            if not truth:
                all_sat = False
                break
        if all_sat:
            result = True
            break
    total_ms = (perf_counter() - start) * 1000
    return result, {
        "detection_ms": detection_ms,
        "component_solver_ms": component_ms,
        "other_overhead_ms": max(0.0, total_ms - detection_ms - component_ms),
        "total_ms": total_ms, "assignments": assignments, "component_calls": calls,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("hard-separator-stress.csv"))
    args = parser.parse_args()
    rows = []
    for width in (2, 3):
        for blocks in (2, 4, 8):
            for core_vars in (18, 26):
                source, meta = make_hard_separator_case(blocks, core_vars, width, 2801)
                reference = independent_sat(source)
                if not reference["glucose3"]:
                    raise AssertionError("planted satisfiable formula rejected")
                direct_samples, full_samples, detection, components, overhead = [], [], [], [], []
                for repeat in range(3):
                    if repeat % 2:
                        result, detail = conditioned_timed(source)
                        before = perf_counter()
                        direct_truth = solve(source)
                        direct_ms = (perf_counter() - before) * 1000
                    else:
                        before = perf_counter()
                        direct_truth = solve(source)
                        direct_ms = (perf_counter() - before) * 1000
                        result, detail = conditioned_timed(source)
                    if not (direct_truth == result == reference["glucose3"]):
                        raise AssertionError("SAT disagreement in stress benchmark")
                    direct_samples.append(direct_ms)
                    full_samples.append(detail["total_ms"])
                    detection.append(detail["detection_ms"])
                    components.append(detail["component_solver_ms"])
                    overhead.append(detail["other_overhead_ms"])
                rows.append({
                    "width": width, "blocks": blocks, "core_vars": core_vars,
                    "source_sha256": source.formula_hash,
                    "variables": source.num_vars, "clauses": source.num_clauses,
                    "direct_median_ms": round(median(direct_samples), 6),
                    "detection_median_ms": round(median(detection), 6),
                    "component_solver_median_ms": round(median(components), 6),
                    "other_overhead_median_ms": round(median(overhead), 6),
                    "conditioned_total_median_ms": round(median(full_samples), 6),
                    "conditioned_faster": median(full_samples) < median(direct_samples),
                    "truth_agrees": True, "lean_verified": False, "promoted": False,
                })
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print({"cases": len(rows),
           "total_runtime_wins": sum(r["conditioned_faster"] for r in rows),
           "max_clauses": max(r["clauses"] for r in rows),
           "median_direct_ms": round(median(r["direct_median_ms"] for r in rows), 4),
           "median_detection_ms": round(median(r["detection_median_ms"] for r in rows), 4),
           "median_component_solver_ms": round(median(r["component_solver_median_ms"] for r in rows), 4),
           "median_other_overhead_ms": round(median(r["other_overhead_median_ms"] for r in rows), 4),
           "median_conditioned_total_ms": round(median(r["conditioned_total_median_ms"] for r in rows), 4),
           "component_solver_only_wins": sum(r["component_solver_median_ms"] < r["direct_median_ms"] for r in rows),
           "all_truths_agree": True, "trusted": False})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
