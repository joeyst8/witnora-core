"""Mine and minimize failures of proposed structural interaction gains."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.adversarial_compression_validation import FAMILIES, make_case
from witnora_core.experimental_operator_search import independent_sat
from witnora_core.operator_counterexamples import (
    apply_sequence, interaction_gain, minimize_counterexample,
)


SEQUENCES = (
    ("bounded_elimination", "bounded_elimination"),
    ("invariant_xor_boundary", "invariant_min_fill"),
    ("invariant_max_release", "parity_root"),
)


def mine(*, sizes=(8, 10), seeds=(29, 37, 41), limit=8):
    evidence = []
    for n in sizes:
        for seed in seeds:
            for family in FAMILIES:
                original = make_case(n, family, seed)
                for sequence in SEQUENCES:
                    gain = interaction_gain(original, sequence)
                    if gain > 0:
                        continue
                    baseline_truth = independent_sat(original)["glucose3"]
                    def failure(candidate):
                        return (candidate.num_clauses >= 3
                                and candidate.num_vars >= 3
                                and interaction_gain(candidate, sequence) <= 0)
                    reduced = minimize_counterexample(
                        original, failure, min_clauses=3,
                        min_variables=3, max_checks=100,
                    )
                    candidate_truth = independent_sat(
                        apply_sequence(reduced, sequence)
                    )["glucose3"]
                    minimized_truth = independent_sat(reduced)["glucose3"]
                    if candidate_truth != minimized_truth:
                        raise AssertionError("candidate changed SAT truth")
                    evidence.append({
                        "hypothesis": "+".join(sequence),
                        "failure_kind": "NO_POSITIVE_INTERACTION_GAIN",
                        "family": family,
                        "size": n,
                        "seed": seed,
                        "original_satisfiable": baseline_truth,
                        "minimized_satisfiable": minimized_truth,
                        "original_sha256": original.formula_hash,
                        "minimized_sha256": reduced.formula_hash,
                        "original_clauses": original.num_clauses,
                        "minimized_clauses": reduced.num_clauses,
                        "minimized_dimacs": reduced.canonical_dimacs(),
                        "minimized_interaction_gain": interaction_gain(reduced, sequence),
                        "lean_verified": False,
                        "novelty_verified": False,
                    })
                    if len(evidence) >= limit:
                        return evidence
    return evidence


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("operator-counterexamples.json"))
    args = parser.parse_args()
    evidence = mine()
    if not evidence:
        raise AssertionError("no negative interaction controls were found")
    args.output.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    print({
        "minimized_counterexamples": len(evidence),
        "original_to_minimized_clauses": [
            (e["original_clauses"], e["minimized_clauses"]) for e in evidence
        ],
        "output": str(args.output),
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
