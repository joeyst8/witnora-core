"""Frozen-sequence out-of-distribution study.

Previously selected operator sequences are applied without retraining to
pigeonhole, graph coloring, 3-XOR Tseitin, N-Queens and planted 3-SAT CNFs.
Structural gains and noisy timing are reported separately.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from statistics import median
from time import perf_counter

from witnora_core.cnf import formula_satisfied
from witnora_core.experimental_operator_search import (
    OPERATORS, TRANSFORMS, independent_sat, structural_score,
)
from witnora_core.ood_sat_families import out_of_distribution_cases
from witnora_core.operator_counterexamples import apply_sequence


# Frozen from the earlier seeded synthetic training/holdout ledger.
FROZEN_SEQUENCES = (
    ("bounded_elimination",),
    ("parity_root",),
    ("bounded_elimination", "bounded_elimination"),
    ("bounded_elimination", "bounded_elimination", "bounded_elimination"),
)
# Fresh structural hypotheses: never treat these as pretrained validation.
EXPLORATORY_SEQUENCES = (
    ("invariant_min_fill",),
    ("invariant_xor_boundary",),
    ("invariant_max_release",),
    ("invariant_xor_boundary", "invariant_min_fill"),
)


def timed_glucose(formula, repeats=3):
    from pysat.solvers import Glucose3
    times = []
    satisfiable = None
    for _ in range(repeats):
        start = perf_counter()
        with Glucose3(bootstrap_with=formula.to_clause_lists()) as solver:
            current = bool(solver.solve())
            model = solver.get_model() if current else None
        elapsed_ms = (perf_counter() - start) * 1000
        if current:
            assignment = {abs(lit): lit > 0 for lit in model or []}
            if not formula_satisfied(formula, assignment):
                raise AssertionError("Glucose3 invalid SAT witness")
        if satisfiable is not None and current != satisfiable:
            raise AssertionError("inconsistent SAT oracle")
        satisfiable = current
        times.append(elapsed_ms)
    return satisfiable, median(times)


def run(seeds, repeats=3):
    observations = []
    for seed in seeds:
        for family, case_id, source, expected in out_of_distribution_cases(seed):
            source_truth = independent_sat(source)
            if expected is not None and source_truth["glucose3"] != expected:
                raise AssertionError(f"generated problem wrong: {case_id}")
            truth, source_ms = timed_glucose(source, repeats)
            if truth != source_truth["glucose3"]:
                raise AssertionError("SAT baselines disagree")
            singles = {
                name: structural_score(source, TRANSFORMS[name](source))
                for name in OPERATORS
            }
            best_single = max(singles.values())
            for category, sequences in (("frozen_holdout", FROZEN_SEQUENCES),
                                        ("exploratory_ood", EXPLORATORY_SEQUENCES)):
                for sequence in sequences:
                    start = perf_counter()
                    result = apply_sequence(source, sequence)
                    transform_ms = (perf_counter() - start) * 1000
                    outcome = independent_sat(result)
                    result_truth, result_ms = timed_glucose(result, repeats)
                    if outcome != source_truth or result_truth != truth:
                        raise AssertionError(f"SAT mismatch: {case_id} {sequence}")
                    structural = structural_score(source, result)
                    observations.append({
                        "seed": seed,
                        "family": family, "case_id": case_id,
                        "test_category": category,
                        "sequence": "+".join(sequence),
                        "source_sha256": source.formula_hash,
                        "residual_sha256": result.formula_hash,
                        "source_variables": source.num_vars,
                        "residual_variables": result.num_vars,
                        "source_clauses": source.num_clauses,
                        "residual_clauses": result.num_clauses,
                        "satisfiable": int(truth),
                        "glucose3_and_minisat22_agree": int(outcome == source_truth),
                        "structural_score": round(structural, 6),
                        "best_single_score": round(best_single, 6),
                        "interaction_gain": round(structural - best_single, 6),
                        "source_glucose3_median_ms": round(source_ms, 6),
                        "transform_ms": round(transform_ms, 6),
                        "residual_glucose3_median_ms": round(result_ms, 6),
                        "complete_experimental_ms": round(transform_ms + result_ms, 6),
                        "timing_repeats": repeats,
                        "lean_checked": 0,
                        "novelty_verified": 0,
                        "promoted": 0,
                    })
    return observations


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, nargs="+", default=[101, 211, 307])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path, default=Path("ood-operator-study.csv"))
    args = parser.parse_args()
    if not args.seeds or args.repeats < 1:
        parser.error("at least one seed and repeat are required")
    rows = run(args.seeds, repeats=args.repeats)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    frozen = [r for r in rows if r["test_category"] == "frozen_holdout"]
    print({
        "records": len(rows), "case_instances": len(args.seeds) * 10,
        "distinct_families": sorted(set(r["family"] for r in rows)),
        "frozen_positive_interactions": sum(r["interaction_gain"] > 0 for r in frozen),
        "frozen_no_gain_or_regressions": sum(r["interaction_gain"] <= 0 for r in frozen),
        "frozen_faster_on_tiny_cases": sum(
            r["complete_experimental_ms"] < r["source_glucose3_median_ms"]
            for r in frozen
        ),
        "timing_is_exploratory": True,
        "all_truths_checked": True,
        "output": str(args.output),
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
