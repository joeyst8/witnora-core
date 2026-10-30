"""Larger, frozen OOD follow-up or explicitly labeled negative-control stress test."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import median
from time import perf_counter

from scripts.benchmark_operator_ood import timed_glucose
from witnora_core.experimental_operator_search import (
    independent_sat, TRANSFORMS, structural_score,
)
from witnora_core.ood_sat_families import larger_unseen_cases
from witnora_core.operator_counterexamples import apply_sequence


def run(screen, seeds=(401, 509), repeats=3, max_sequences=2):
    if not screen:
        raise ValueError("empty preregistered candidate screen")
    approved = [x for x in screen if x["followup_recommended"]]
    selected = approved[:max_sequences] if approved else screen[:max_sequences]
    # A failed screen can still be stress-tested as a negative control.
    selection = "FOLLOWUP_EXPERIMENTAL" if approved else "NO_SURVIVOR_NEGATIVE_CONTROL"
    results = []
    for seed in seeds:
        for family, case_id, original, expected in larger_unseen_cases(seed):
            oracle = independent_sat(original)
            if expected is not None and oracle["glucose3"] != expected:
                raise AssertionError(f"incorrect generated case: {case_id}")
            truth, source_ms = timed_glucose(original, repeats)
            if truth != oracle["glucose3"]:
                raise AssertionError("original solver disagreement")
            best_single = max(structural_score(original, op(original))
                              for op in TRANSFORMS.values())
            for candidate in selected:
                sequence = tuple(candidate["sequence"].split("+"))
                start = perf_counter()
                transformed = apply_sequence(original, sequence)
                prep_ms = (perf_counter() - start) * 1000
                outcome = independent_sat(transformed)
                reduced_truth, reduced_ms = timed_glucose(transformed, repeats)
                if outcome != oracle or reduced_truth != truth:
                    raise AssertionError("original/transformed satisfiability mismatch")
                score = structural_score(original, transformed)
                results.append({
                    "seed": seed,
                    "family": family, "case_id": case_id,
                    "sequence": "+".join(sequence),
                    "screen_selection": selection,
                    "screen_followup_flag": bool(candidate["followup_recommended"]),
                    "source_sha256": original.formula_hash,
                    "transformed_sha256": transformed.formula_hash,
                    "source_variables": original.num_vars,
                    "source_clauses": original.num_clauses,
                    "transformed_variables": transformed.num_vars,
                    "transformed_clauses": transformed.num_clauses,
                    "satisfiable": int(truth),
                    "structural_score": round(score, 6),
                    "best_single_score": round(best_single, 6),
                    "interaction_gain": round(score - best_single, 6),
                    "source_glucose_median_ms": round(source_ms, 6),
                    "preprocess_ms": round(prep_ms, 6),
                    "transformed_glucose_median_ms": round(reduced_ms, 6),
                    "total_experimental_ms": round(prep_ms + reduced_ms, 6),
                    "repeats": repeats,
                    "independent_solver_agreement": True,
                    "lean_verified": False,
                    "novelty_verified": False,
                    "promoted": False,
                })
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--screen", type=Path, default=Path("ood-candidate-screen.json"))
    parser.add_argument("--output", type=Path, default=Path("ood-larger-stress.csv"))
    parser.add_argument("--seeds", type=int, nargs="+", default=[401, 509])
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    screen = json.loads(args.screen.read_text(encoding="utf-8"))
    if not isinstance(screen, list):
        raise ValueError("candidate screen must be a list")
    records = run(screen, seeds=args.seeds, repeats=args.repeats)
    if not records:
        raise AssertionError("no larger OOD cases")
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    print({
        "records": len(records),
        "larger_cases": len(args.seeds) * 8,
        "screen_selection": records[0]["screen_selection"],
        "sequences": sorted(set(row["sequence"] for row in records)),
        "positive_interactions": sum(row["interaction_gain"] > 0 for row in records),
        "no_gain_or_regressions": sum(row["interaction_gain"] <= 0 for row in records),
        "total_time_beats_original": sum(
            row["total_experimental_ms"] < row["source_glucose_median_ms"]
            for row in records),
        "all_satisfiability_checked": True,
        "novelty_proven": False,
        "output": str(args.output),
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
