"""Predeclared, fail-closed screen of unseen-family operator experiments."""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import median


def screen(rows):
    by_seq = defaultdict(list)
    for row in rows:
        if row["test_category"] != "frozen_holdout":
            continue
        if row["glucose3_and_minisat22_agree"] != "1":
            raise ValueError("unverified independent SAT agreement")
        by_seq[row["sequence"]].append(row)
    rankings = []
    for sequence, cases in sorted(by_seq.items()):
        family_gains = defaultdict(list)
        for case in cases:
            family_gains[case["family"]].append(float(case["interaction_gain"]))
        families_with_positive_gain = sorted(
            family for family, gains in family_gains.items() if
            median(gains) > 0
        )
        positive_cases = sum(float(case["interaction_gain"]) > 0 for case in cases)
        negative_cases = sum(float(case["interaction_gain"]) <= 0 for case in cases)
        performance_wins = sum(
            float(case["complete_experimental_ms"]) <
            float(case["source_glucose3_median_ms"])
            for case in cases
        )
        # High bar for *follow-up only*: at least three distinct unseen
        # families, majority of cases, and no oracle disagreements.
        followup = (len(families_with_positive_gain) >= 3 and
                    positive_cases > negative_cases)
        rankings.append({
            "sequence": sequence,
            "cases": len(cases),
            "families_with_positive_median_interaction": families_with_positive_gain,
            "positive_interaction_cases": positive_cases,
            "no_gain_or_negative_cases": negative_cases,
            "experimental_total_time_wins": performance_wins,
            "median_interaction_gain": median(
                float(case["interaction_gain"]) for case in cases),
            "followup_recommended": followup,
            "status": "INVESTIGATE_UNVERIFIED" if followup
                      else "HOLD_NO_EVIDENCE_OF_GENERALIZATION",
            "novelty_verified": False,
            "lean_verified": False,
            "performance_advantage_verified": False,
            "promoted": False,
        })
    return sorted(rankings, key=lambda row: (
        -len(row["families_with_positive_median_interaction"]),
        -row["positive_interaction_cases"], row["sequence"],
    ))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("ood-operator-study.csv"))
    parser.add_argument("--output", type=Path, default=Path("ood-candidate-screen.json"))
    args = parser.parse_args()
    with args.input.open(newline="", encoding="utf-8") as file:
        records = list(csv.DictReader(file))
    if not records:
        raise AssertionError("missing OOD measurements")
    rankings = screen(records)
    if not rankings:
        raise AssertionError("no frozen candidate sequences evaluated")
    args.output.write_text(json.dumps(rankings, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print({
        "ranked_sequences": len(rankings),
        "followup_only": [r["sequence"] for r in rankings
                          if r["followup_recommended"]],
        "no_generalization_evidence": [r["sequence"] for r in rankings
                                       if not r["followup_recommended"]],
        "output": str(args.output),
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
