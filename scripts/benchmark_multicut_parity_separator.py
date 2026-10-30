"""Planted and unseen multi-variable parity-cut challenge."""
from __future__ import annotations

import csv
from pathlib import Path

from witnora_core.cnf import CNFFormula
from witnora_core.multicut_parity_separator import bounded_parity_separators
from witnora_core.ood_sat_families import larger_unseen_cases
from witnora_core.xor import canonical_xor_cnf_clauses


def planted(cut):
    return CNFFormula.from_raw_clauses(
        canonical_xor_cnf_clauses((1, 2, *cut), 0)
        | canonical_xor_cnf_clauses((*cut, 10, 11), 1))


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("multicut-parity-study.csv"))
    args = parser.parse_args()
    cases = [
        ("planted", "two_variable_cut", planted((3, 4)), 2),
        ("planted", "three_variable_cut", planted((3, 4, 5)), 3),
    ]
    for seed in (2141, 2267):
        for family, case_id, formula, _ in larger_unseen_cases(seed):
            cases.append((family, f"{case_id}_seed{seed}", formula, None))
    rows = []
    for family, case_id, formula, expected in cases:
        result = bounded_parity_separators(formula)
        if expected is not None and result["smallest_cut_size"] != expected:
            raise AssertionError(f"planted cut not recovered: {case_id}")
        rows.append({
            "family": family, "case_id": case_id,
            "source_sha256": result["source_sha256"],
            "equations": result["exact_parity_equations"],
            "cuts": result["candidate_count"],
            "smallest_cut": result["smallest_cut_size"],
            "trials": result["trials"],
            "exhausted": result["budget_exhausted"],
            "full_cnf_separator_verified": False,
            "lean_verified": False, "promoted": False,
        })
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print({"cases": len(rows), "ood_cases": len(rows) - 2,
           "ood_with_multicuts": sum(x["cuts"] > 0 for x in rows[2:]),
           "planted_two_cut": rows[0]["smallest_cut"] == 2,
           "planted_three_cut": rows[1]["smallest_cut"] == 3,
           "trusted": False})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
