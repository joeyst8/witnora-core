"""Finite conditioned solving versus direct independent SAT baseline."""
from __future__ import annotations

import csv
from pathlib import Path
from time import perf_counter

from pysat.solvers import Glucose3
from witnora_core.experimental_operator_search import independent_sat
from witnora_core.hidden_separator_challenge import make_hidden_separator
from witnora_core.ood_sat_families import larger_unseen_cases
from witnora_core.separator_conditioned_solve import solve_conditioned


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("separator-conditioned-study.csv"))
    args = parser.parse_args()
    cases = []
    for seed in (107, 227, 347, 467):
        for width in (2, 3):
            for cross in (False, True):
                f, _ = make_hidden_separator(seed, width=width, cross_noise=cross)
                cases.append(("controlled", f"w{width}_cross{int(cross)}_seed{seed}", f))
    for seed in (2371, 2447):
        for family, case_id, formula, _ in larger_unseen_cases(seed):
            cases.append((family, f"{case_id}_seed{seed}", formula))
    rows = []
    for family, case_id, formula in cases:
        start = perf_counter()
        with Glucose3(bootstrap_with=formula.to_clause_lists()) as solver:
            direct_truth = bool(solver.solve())
        direct_ms = (perf_counter() - start) * 1000
        baseline = independent_sat(formula)
        if direct_truth != baseline["glucose3"]:
            raise AssertionError("direct solver disagrees with independent oracle")
        start = perf_counter()
        result = solve_conditioned(formula)
        conditioned_ms = (perf_counter() - start) * 1000
        if result["satisfiable"] != baseline["glucose3"]:
            raise AssertionError(f"conditioning changed SAT truth: {case_id}")
        rows.append({
            "family": family, "case_id": case_id,
            "source_sha256": formula.formula_hash,
            "mode": result["mode"], "cut_size": len(result["cut"]),
            "assignments_examined": result["assignments_examined"],
            "component_calls": result["component_calls"],
            "direct_glucose_ms": round(direct_ms, 6),
            "conditioned_ms": round(conditioned_ms, 6),
            "truth_agrees": True,
            "lean_verified": False, "promoted": False,
        })
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print({"cases": len(rows), "conditioned_cases": sum(r["mode"] == "conditioned" for r in rows),
           "runtime_wins_vs_direct_glucose": sum(r["conditioned_ms"] < r["direct_glucose_ms"] for r in rows),
           "all_truths_agree": True, "trusted": False})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
