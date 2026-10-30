"""Fresh OOD falsification of bounded assumption-based simplification."""
from __future__ import annotations

import csv
from pathlib import Path
from time import perf_counter

from scripts.benchmark_operator_ood import timed_glucose
from witnora_core.experimental_operator_search import independent_sat, structural_score, unit_propagation
from witnora_core.forced_relation_probe import probe_forced_relations
from witnora_core.ood_sat_families import larger_unseen_cases


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("forced-relation-probe.csv"))
    args = parser.parse_args()
    rows = []
    for seed in (1783, 1871):
        for family, case_id, source, expected in larger_unseen_cases(seed):
            truth = independent_sat(source)
            if expected is not None and truth["glucose3"] != expected:
                raise AssertionError("incorrect source truth")
            for name, operator in (
                ("unit_only", lambda: (unit_propagation(source), {})),
                ("failed_literal_probe", lambda: probe_forced_relations(source)),
            ):
                start = perf_counter()
                result, info = operator()
                prep_ms = (perf_counter() - start) * 1000
                if independent_sat(result) != truth:
                    raise AssertionError(f"SAT mismatch {case_id} {name}")
                solved, solve_ms = timed_glucose(result, 3)
                if solved != truth["glucose3"]:
                    raise AssertionError("timed solver mismatch")
                rows.append({
                    "seed": seed, "family": family, "case_id": case_id,
                    "strategy": name, "source_sha256": source.formula_hash,
                    "candidate_sha256": result.formula_hash,
                    "structural_gain": round(structural_score(source, result), 6),
                    "forced_count": len(info.get("forced_literals", [])),
                    "probed_variables": info.get("checked_variables", 0),
                    "preprocess_ms": round(prep_ms, 6),
                    "total_ms": round(prep_ms + solve_ms, 6),
                    "oracle_agreement": True, "lean_verified": False,
                    "novelty_verified": False, "promoted": False,
                })
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    groups = {}
    for row in rows:
        groups.setdefault((row["seed"], row["case_id"]), {})[row["strategy"]] = row
    print({
        "cases": len(groups),
        "structural_wins": sum(
            g["failed_literal_probe"]["structural_gain"] > g["unit_only"]["structural_gain"]
            for g in groups.values()),
        "runtime_wins": sum(
            g["failed_literal_probe"]["total_ms"] < g["unit_only"]["total_ms"]
            for g in groups.values()),
        "cases_with_forced_literals": sum(
            g["failed_literal_probe"]["forced_count"] > 0
            for g in groups.values()),
        "independent_oracles_agree": True,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
