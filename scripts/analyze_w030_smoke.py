"""Transparent descriptive cost analysis for the frozen W030 eight-case smoke.

All calculations are on three-repeat per-case medians. With one matched
SAT/UNSAT seed at each order there is NO inferential confidence interval.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys


ARMS = ("kissat", "w027_plus_kissat", "w030_prefix_plus_kissat")


def analyze(report):
    if report.get("study") != "W-CROSSDOMAIN-030" or report.get("phase") != "exploratory_smoke_not_full_protocol":
        raise ValueError("W030 exploratory smoke report required")
    n = report["case_count"]
    if len(report["rows"]) != n * 3 * len(ARMS):
        raise ValueError("not all precommitted timed invocations are present")

    by_case = {}
    for row in report["per_case_arm_medians"]:
        by_case.setdefault(row["case_id"], {})[row["arm"]] = row
    labels = {}
    for row in report["rows"]:
        if row["verdict"] != row["expected"]:
            raise ValueError("wrong or censored result in smoke")
        labels.setdefault(row["case_id"], row["expected"])
        if labels[row["case_id"]] != row["expected"]:
            raise ValueError("inconsistent frozen label")
    if len(by_case) != n or len(labels) != n:
        raise ValueError("case count mismatch")

    probes = {p["case_id"]: p for p in report["static_prefix_checks"]}
    result = []
    for name, arms in by_case.items():
        if set(arms) != set(ARMS):
            raise ValueError("missing solver arm")
        if any(arms[a]["solved_repetitions"] != 3 for a in ARMS):
            raise ValueError("missing solved repetitions")
        k, old, new = [arms[a]["median_solved_wall_ns"] / 1e6 for a in ARMS]
        probe = probes[name]
        result.append({
            "case_id": name, "expected": labels[name],
            "kissat_ms": k, "w027_ms": old, "w030_ms": new,
            "kissat_over_w030_ratio": k / new,
            "w027_over_w030_ratio": old / new,
            "clauses_total": probe["declared_clauses"],
            "clauses_read_by_w030": probe["read_clauses"],
            "prefix_read_fraction": probe["read_clauses"] / probe["declared_clauses"],
        })
    result.sort(key=lambda r: r["case_id"])

    means = {key: sum(r[key] for r in result) / len(result)
             for key in ("kissat_ms", "w027_ms", "w030_ms")}
    break_even = []
    for arrangement in ("corefirst", "corelast"):
        prefix = f"w030_d8192_r0_"
        sat = next(r for r in result if r["case_id"] == prefix + "sat_" + arrangement)
        unsat = next(r for r in result if r["case_id"] == prefix + "unsat_" + arrangement)
        penalty = sat["w030_ms"] - sat["kissat_ms"]
        saving = unsat["kissat_ms"] - unsat["w030_ms"]
        break_even.append({"arrangement": arrangement,
                           "sat_overhead_ms": penalty,
                           "unsat_saving_ms": saving,
                           "illustrative_unsat_fraction_to_break_even": penalty / (penalty + saving),
                           "matched_seed_count": 1,
                           "inference": "single matched seed, descriptive only"})

    return {
        "study": "W-CROSSDOMAIN-030", "analysis": "exploratory_eight_case_cost_inclusive",
        "case_count": n, "timed_invocations": len(report["rows"]),
        "cases": result,
        "equal_case_weight_mean_ms": means,
        "w030_extra_vs_kissat_percent": 100 * (means["w030_ms"] / means["kissat_ms"] - 1),
        "w030_saving_vs_w027_percent": 100 * (1 - means["w030_ms"] / means["w027_ms"]),
        "w030_faster_than_kissat_unsat_cases": sum(r["expected"] == "UNSAT" and r["w030_ms"] < r["kissat_ms"] for r in result),
        "w030_faster_than_kissat_sat_cases": sum(r["expected"] == "SAT" and r["w030_ms"] < r["kissat_ms"] for r in result),
        "illustrative_d8192_order_break_even": break_even,
        "claim_scope": "only eight precommitted CNFs and three repeats per arm; no cross-domain effect inference or claim about P=NP",
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m scripts.analyze_w030_smoke <raw-W030-smoke.json>")
    source = json.loads(Path(sys.argv[1]).read_text())
    print(json.dumps(analyze(source), indent=2, sort_keys=True))
