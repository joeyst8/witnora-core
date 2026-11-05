"""Rank measured lookahead failures without relabeling them discoveries."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def analyze(rows: list[dict]) -> dict:
    grouped = {}
    for row in rows:
        key = (int(row["seed"]), row["case_id"])
        slot = grouped.setdefault(key, {})
        label = row["strategy"]
        if label in slot:
            raise ValueError(f"duplicate strategy {key} {label}")
        slot[label] = row
    outcomes = []
    for (seed, case_id), strategies in sorted(grouped.items()):
        if set(strategies) != {"greedy_two_steps", "speculative_two_ply"}:
            raise ValueError(f"missing experiment comparison: {case_id}")
        greedy, speculative = (
            strategies["greedy_two_steps"], strategies["speculative_two_ply"])
        if not (str(greedy["independent_solver_agreement"]).lower() in ("1", "true")
                and str(speculative["independent_solver_agreement"]).lower() in ("1", "true")):
            raise ValueError("independent SAT oracle agreement missing")
        score_delta = (float(speculative["structural_gain"]) -
                       float(greedy["structural_gain"]))
        time_delta = float(speculative["total_ms"]) - float(greedy["total_ms"])
        outcomes.append({
            "seed": seed, "case_id": case_id, "family": greedy["family"],
            "structural_delta_over_greedy": round(score_delta, 6),
            "total_time_delta_ms_over_greedy": round(time_delta, 6),
            "structural_regression": score_delta < 0,
            "end_to_end_slowdown": time_delta > 0,
            "source_sha256": greedy["source_sha256"],
        })
    structural_losses = sorted((row for row in outcomes
                                if row["structural_regression"]),
                               key=lambda x: (x["structural_delta_over_greedy"],
                                              x["family"], x["case_id"], x["seed"]))
    runtime_losses = sorted((row for row in outcomes
                             if row["end_to_end_slowdown"]),
                            key=lambda x: (-x["total_time_delta_ms_over_greedy"],
                                           x["family"], x["case_id"], x["seed"]))
    return {
        "evaluated_cases": len(outcomes),
        "structural_losses": len(structural_losses),
        "runtime_slowdowns": len(runtime_losses),
        "worst_structural_examples": structural_losses[:5],
        "worst_runtime_examples": runtime_losses[:5],
        "candidate_proven_novel": False,
        "candidate_proven_faster": False,
        "trusted": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("lookahead-pivot-study.csv"))
    parser.add_argument("--output", type=Path, default=Path("lookahead-failure-report.json"))
    args = parser.parse_args()
    with args.input.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError("missing comparison observations")
    report = analyze(rows)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print({k: report[k] for k in ("evaluated_cases", "structural_losses",
                                 "runtime_slowdowns")})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
