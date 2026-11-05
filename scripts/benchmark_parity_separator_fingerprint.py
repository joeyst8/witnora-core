"""Discovery-only comparison on planted and unfamiliar formulas."""
from __future__ import annotations

import csv
from pathlib import Path

from witnora_core.cnf import CNFFormula
from witnora_core.ood_sat_families import larger_unseen_cases
from witnora_core.parity_separator_fingerprint import parity_separator_fingerprint
from witnora_core.xor import canonical_xor_cnf_clauses


def planted(bridge: bool):
    first = canonical_xor_cnf_clauses((1, 2, 3), 0)
    second = canonical_xor_cnf_clauses((3 if bridge else 6, 4, 5), 1)
    return CNFFormula.from_raw_clauses(first | second)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("parity-separator-fingerprint.csv"))
    args = parser.parse_args()
    cases = [
        ("planted", "single_shared_variable", planted(True), True),
        ("negative_control", "disjoint_parity_blocks", planted(False), False),
    ]
    for seed in (1987, 2053):
        for family, case_id, formula, _ in larger_unseen_cases(seed):
            cases.append((family, f"{case_id}_seed{seed}", formula, None))
    rows = []
    for family, case_id, formula, expected in cases:
        fingerprint = parity_separator_fingerprint(formula)
        if expected is not None and bool(fingerprint["candidate_count"]) != expected:
            raise AssertionError(f"incorrect planted bridge classification {case_id}")
        rows.append({
            "family": family, "case_id": case_id,
            "source_sha256": fingerprint["source_sha256"],
            "exact_parity_equations": fingerprint["exact_parity_equations"],
            "separator_candidates": fingerprint["candidate_count"],
            "candidate_variables": "|".join(str(x["variable"]) for x in fingerprint["separator_candidates"]),
            "expected_candidate": "" if expected is None else int(expected),
            "complete_cnf_separator_verified": False,
            "novelty_verified": False, "promoted": False,
        })
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print({"cases": len(rows), "ood_cases": len(rows) - 2,
           "ood_with_candidates": sum(r["separator_candidates"] > 0 for r in rows[2:]),
           "planted_positive_detected": rows[0]["separator_candidates"] > 0,
           "disjoint_negative_rejected": rows[1]["separator_candidates"] == 0,
           "trusted": False})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
