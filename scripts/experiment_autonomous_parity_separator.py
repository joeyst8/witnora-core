"""Blind parity separator discovery versus structured and null controls."""
from __future__ import annotations

import json
from pathlib import Path
from random import Random

from witnora_core.cnf import CNFFormula
from witnora_core.hidden_separator_challenge import make_hidden_separator
from witnora_core.autonomous_parity_separator import (
    discover_repaired_separator,
    full_cnf_groups_separated,
)


def _random_three_sat(seed: int) -> CNFFormula:
    rng = Random(73000 + seed)
    clauses = []
    for _ in range(24):
        variables = rng.sample(range(1, 11), 3)
        clauses.append([v if rng.getrandbits(1) else -v for v in variables])
    return CNFFormula.from_raw_clauses(clauses)


def _bridged_controls(seed: int) -> CNFFormula:
    base, metadata = make_hidden_separator(seed, width=2, cross_noise=True)
    # Multiple extra cross-links deliberately defeat a tiny repair budget.
    left = metadata["left_block"]
    right = metadata["right_block"]
    rows = base.to_clause_lists()
    for i in range(3):
        rows.append([left[i], right[i], 500 + seed * 5 + i])
    return CNFFormula.from_raw_clauses(rows)


def _dense_bridge_negative(seed: int) -> CNFFormula:
    base, metadata = make_hidden_separator(seed, width=2, cross_noise=False)
    left, right = metadata["left_block"], metadata["right_block"]
    rows = base.to_clause_lists()
    # A complete bipartite 3x3 cross-connection requires at least
    # three extra removals to separate these preserved parity groups.
    for u in left:
        for v in right:
            rows.append([u, v])
    return CNFFormula.from_raw_clauses(rows)


def run_experiment(seed_count: int = 8):
    if not 1 <= seed_count <= 24:
        raise ValueError("seed count out of range")
    records = []
    for width in (2, 3):
        for noisy in (False, True):
            for seed in range(seed_count):
                formula, metadata = make_hidden_separator(
                    seed, width=width, cross_noise=noisy)
                result = discover_repaired_separator(formula)
                records.append({
                    "family": "hidden_separator", "seed": seed,
                    "width": width, "cross_noise": noisy,
                    "ground_truth_boundary": list(metadata["boundary"]),
                    "detected": result["status"] == "FOUND",
                    "result": result,
                })
    for family, generate in [
        ("random_3sat", _random_three_sat),
        ("bridged_stress", _bridged_controls),
        ("dense_bridge_negative", _dense_bridge_negative),
    ]:
        for seed in range(seed_count):
            formula = generate(seed)
            result = discover_repaired_separator(formula)
            records.append({
                "family": family, "seed": seed,
                "detected": result["status"] == "FOUND",
                "result": result,
            })
    summary = {
        "total": len(records),
        "hidden_total": sum(r["family"] == "hidden_separator" for r in records),
        "hidden_detected": sum(
            r["detected"] for r in records
            if r["family"] == "hidden_separator"),
        "hidden_noisy_detected": sum(
            r["detected"] for r in records
            if r["family"] == "hidden_separator" and r["cross_noise"]),
        "random_3sat_detected": sum(
            r["detected"] for r in records if r["family"] == "random_3sat"),
        "bridged_stress_detected": sum(
            r["detected"] for r in records if r["family"] == "bridged_stress"),
        "dense_bridge_negative_detected": sum(
            r["detected"] for r in records
            if r["family"] == "dense_bridge_negative"),
        "mean_candidate_trials": round(sum(
            r["result"]["trials"] for r in records) / len(records), 2),
        "ground_truth_not_provided_to_detector": True,
        "formal_novelty_established": False,
    }
    return {"summary": summary, "records": records}


def main():
    result = run_experiment()
    path = Path("research/autonomous_parity_separator_results.json")
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
