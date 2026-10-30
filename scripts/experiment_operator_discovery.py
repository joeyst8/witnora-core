"""Train/hold-out experiment ledger for Witnora transformation hypotheses.

The training split discovers promising operator sequences. The held-out
split tests whether their structural reduction transfers to fresh seeds.
All claims remain experimental; SAT truth is checked independently.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean

from scripts.adversarial_compression_validation import FAMILIES, make_case
from witnora_core.experimental_operator_search import (
    TRANSFORMS, assess_hypothesis, explore_operators,
    structural_score, Hypothesis,
)


def run(*, sizes=(6, 10), train_seeds=(7, 13), holdout_seeds=(29, 37),
        beam_width=8, depth=3):
    if set(train_seeds) & set(holdout_seeds):
        raise ValueError("train and holdout seeds must be disjoint")
    if not train_seeds or not holdout_seeds:
        raise ValueError("train and holdout cannot be empty")
    training = []
    candidates_by_sequence = {}
    for n in sizes:
        for seed in train_seeds:
            for family in FAMILIES:
                original = make_case(n, family, seed)
                for hypothesis in explore_operators(original, depth=depth,
                                                    beam_width=beam_width)[:3]:
                    checked = assess_hypothesis(original, hypothesis)
                    if not checked["oracle_agreement"]:
                        raise AssertionError("transformation candidate changed SAT truth")
                    checked.update(split="train", size=n, seed=seed, family=family)
                    training.append(checked)
                    seq = tuple(hypothesis.sequence)
                    candidates_by_sequence.setdefault(seq, set()).add(family)
    # Retain sequences with observed reductions on at least two distinct
    # families. This is a selection heuristic, not a scientific novelty test.
    retained = sorted((seq for seq, families in candidates_by_sequence.items()
                       if len(families) >= 2),
                      key=lambda seq: (len(seq), seq))
    holdout = []
    for n in sizes:
        for seed in holdout_seeds:
            for family in FAMILIES:
                original = make_case(n, family, seed)
                for seq in retained:
                    transformed = original
                    for op in seq:
                        transformed = TRANSFORMS[op](transformed)
                    hypothesis = Hypothesis(seq, transformed,
                                            structural_score(original, transformed))
                    checked = assess_hypothesis(original, hypothesis)
                    if not checked["oracle_agreement"]:
                        raise AssertionError("held-out SAT disagreement")
                    checked.update(split="holdout", size=n, seed=seed, family=family)
                    holdout.append(checked)
    return training + holdout, retained


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", type=int, nargs="+", default=[6, 10])
    parser.add_argument("--train-seeds", type=int, nargs="+", default=[7, 13])
    parser.add_argument("--holdout-seeds", type=int, nargs="+", default=[29, 37])
    parser.add_argument("--output", type=Path, default=Path("operator-discovery-ledger.csv"))
    parser.add_argument("--beam", type=int, default=8)
    parser.add_argument("--depth", type=int, default=3)
    args = parser.parse_args()
    records, sequences = run(
        sizes=args.sizes, train_seeds=args.train_seeds,
        holdout_seeds=args.holdout_seeds,
        beam_width=args.beam, depth=args.depth,
    )
    if not records:
        raise AssertionError("operator experiment produced no candidates")
    output = args.output
    fields = sorted({key for row in records for key in row})
    with output.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow({**record,
                             "operator_sequence": "+".join(record["operator_sequence"])})
    summary = {
        "training_records": sum(row["split"] == "train" for row in records),
        "holdout_records": sum(row["split"] == "holdout" for row in records),
        "retained_sequences": ["+".join(seq) for seq in sequences],
        "holdout_mean_structural_score": (
            mean(row["structural_score"] for row in records if row["split"] == "holdout")
            if any(row["split"] == "holdout" for row in records) else None
        ),
        "all_oracles_agree": all(row["oracle_agreement"] for row in records),
        "lean_verified": False,
        "novelty_verified": False,
        "output": str(output),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
