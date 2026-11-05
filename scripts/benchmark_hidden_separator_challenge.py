"""Blind seeded challenge; detector never receives planted boundary labels."""
from __future__ import annotations

import csv
from pathlib import Path

from witnora_core.hidden_separator_challenge import (
    make_hidden_separator, independent_parity_cut_width, full_cnf_anchors_separated,
)
from witnora_core.multicut_parity_separator import bounded_parity_separators
from witnora_core.xor import detect_cnf_xor_patterns


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("hidden-separator-challenge.csv"))
    args = parser.parse_args()
    rows = []
    for seed in (103, 211, 307, 419, 523, 631):
        for width in (2, 3):
            for cross_noise in (False, True):
                formula, hidden = make_hidden_separator(
                    seed, width=width, cross_noise=cross_noise)
                predicted = bounded_parity_separators(formula)
                supports = [tuple(eq.variables)
                            for eq in detect_cnf_xor_patterns(formula).equations]
                oracle_width = independent_parity_cut_width(supports)
                boundary_recalled = list(hidden["boundary"]) in [
                    c["variables"] for c in predicted["candidate_cuts"]]
                if predicted["smallest_cut_size"] != oracle_width or not boundary_recalled:
                    raise AssertionError("hidden parity separator mismatch")
                full_separated = full_cnf_anchors_separated(
                    formula, hidden["boundary"],
                    hidden["left_anchor"], hidden["right_anchor"])
                if full_separated == cross_noise:
                    raise AssertionError("cross-noise separation audit failed")
                rows.append({
                    "seed": seed, "source_sha256": formula.formula_hash,
                    "planted_width": width, "cross_noise": cross_noise,
                    "predicted_min_width": predicted["smallest_cut_size"],
                    "independent_oracle_width": oracle_width,
                    "hidden_boundary_recalled": boundary_recalled,
                    "full_cnf_anchors_separated": full_separated,
                    "parity_only_candidate": True,
                    "promoted": False,
                })
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print({
        "cases": len(rows),
        "hidden_boundaries_recalled": sum(r["hidden_boundary_recalled"] for r in rows),
        "full_cnf_separators": sum(r["full_cnf_anchors_separated"] for r in rows),
        "cross_noise_rejections": sum(r["cross_noise"] and not r["full_cnf_anchors_separated"] for r in rows),
        "trusted": False,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
