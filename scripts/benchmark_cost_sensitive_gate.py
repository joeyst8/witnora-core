"""Frozen-train/holdout cost-sensitive gate study; no holdout fitting."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from time import perf_counter

from scripts.benchmark_operator_ood import timed_glucose
from witnora_core.adaptive_lookahead_prototype import adaptive_pivot
from witnora_core.cost_sensitive_gate import choose_threshold, cost_sensitive_pivot
from witnora_core.experimental_operator_search import bounded_elimination, independent_sat, structural_score
from witnora_core.ood_sat_families import larger_unseen_cases
from witnora_core.selective_lookahead_prototype import cheap_pivot_features


def measure(operator, source, repeats):
    start = perf_counter()
    result = operator()
    prep_ms = (perf_counter() - start) * 1000
    truth = independent_sat(result)
    solved, solve_ms = timed_glucose(result, repeats)
    if solved != truth["glucose3"]:
        raise AssertionError("solver disagreement")
    return result, prep_ms + solve_ms, truth


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("cost-sensitive-holdout.csv"))
    parser.add_argument("--model", type=Path, default=Path("cost-sensitive-model.json"))
    args = parser.parse_args()
    training = []
    for seed in (1301, 1423):
        for _, _, source, expected in larger_unseen_cases(seed):
            original = independent_sat(source)
            if expected is not None and original["glucose3"] != expected:
                raise AssertionError("incorrect training source")
            greedy, greedy_ms, truth = measure(
                lambda: bounded_elimination(bounded_elimination(source)), source, 3)
            adaptive, adaptive_ms, adapted_truth = measure(
                lambda: adaptive_pivot(source, expansion_budget=24)[0], source, 3)
            if truth != original or adapted_truth != original:
                raise AssertionError("training truth mismatch")
            features = cheap_pivot_features(source)
            training.append({
                "mixed_pivots": features["viable_mixed_pivots"],
                "variables": source.num_vars, "clauses": source.num_clauses,
                "greedy_score": structural_score(source, greedy),
                "adaptive_score": structural_score(source, adaptive),
                "greedy_ms": greedy_ms, "adaptive_ms": adaptive_ms,
            })
    fit = choose_threshold(training, cost_weight=2)
    args.model.write_text(json.dumps(fit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print({"frozen_threshold": fit["threshold"], "train_cases": fit["train_cases"],
           "selected_train_cases": fit["selected_train_cases"]})

    rows = []
    for seed in (1549, 1663):
        for family, case_id, source, expected in larger_unseen_cases(seed):
            original = independent_sat(source)
            if expected is not None and original["glucose3"] != expected:
                raise AssertionError("incorrect holdout source")
            for name, method in (
                ("greedy", lambda: bounded_elimination(bounded_elimination(source))),
                ("adaptive", lambda: adaptive_pivot(source, expansion_budget=24)[0]),
                ("frozen_gate", lambda: cost_sensitive_pivot(source, threshold=fit["threshold"])[0]),
            ):
                result, elapsed, truth = measure(method, source, 3)
                if truth != original:
                    raise AssertionError("holdout truth mismatch")
                rows.append({
                    "seed": seed, "family": family, "case_id": case_id,
                    "strategy": name, "source_sha256": source.formula_hash,
                    "candidate_sha256": result.formula_hash,
                    "structural_gain": round(structural_score(source, result), 6),
                    "total_ms": round(elapsed, 6),
                    "oracle_agreement": True, "lean_verified": False,
                    "promoted": False,
                })
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    groups = {}
    for row in rows:
        groups.setdefault((row["seed"], row["case_id"]), {})[row["strategy"]] = row
    for baseline in ("greedy", "adaptive"):
        print({f"gate_structural_wins_vs_{baseline}": sum(
            g["frozen_gate"]["structural_gain"] > g[baseline]["structural_gain"]
            for g in groups.values()),
            f"gate_runtime_wins_vs_{baseline}": sum(
                g["frozen_gate"]["total_ms"] < g[baseline]["total_ms"]
                for g in groups.values()), "holdout_cases": len(groups)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
