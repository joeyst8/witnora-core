"""Preregistered censoring-aware W032 external-case analysis.

Do not average timeout-censored cases as if they were solved. No statistical
performance gain is claimed from the tiny joint-solved subset.
"""

from __future__ import annotations

import json
from pathlib import Path
import statistics
import sys


ARMS = ("kissat", "w027_plus_kissat", "w030_prefix_plus_kissat")
REPEATS = 3


def analyze(raw):
    if raw.get("study") != "W-CROSSDOMAIN-032" or raw.get("phase") != "frozen_external_domain_pilot":
        raise ValueError("only W032 frozen external pilot allowed")
    if raw.get("case_count") != 14 or raw.get("external_case_count") != 8:
        raise ValueError("frozen case count mismatch")
    if len(raw["rows"]) != 14 * len(ARMS) * REPEATS:
        raise ValueError("missing preregistered invocations")
    for row in raw["rows"]:
        if row["verdict"] not in (row["expected"], "TIMEOUT"):
            raise ValueError("mismatched, erroneous or unrecognized source verdict")

    external = [r for r in raw["rows"] if r["stratum"] == "official_external_vlsat2"]
    by_arm = {}
    for arm in ARMS:
        subset = [r for r in external if r["arm"] == arm]
        by_arm[arm] = {"solved_invocations": sum(r["verdict"] in ("SAT", "UNSAT") for r in subset),
                       "timeouts": sum(r["verdict"] == "TIMEOUT" for r in subset),
                       "errors": sum(r["verdict"] not in ("SAT", "UNSAT", "TIMEOUT") for r in subset)}
        if len(subset) != 8 * REPEATS:
            raise ValueError("missing external arm rows")

    bycase = {}
    for row in raw["per_case_arm_medians"]:
        bycase.setdefault(row["case_id"], {})[row["arm"]] = row
    fully_matched = []
    for name, entries in bycase.items():
        one = entries["kissat"]
        if one["stratum"] != "official_external_vlsat2":
            continue
        if set(entries) != set(ARMS):
            raise ValueError("missing solver arm")
        if all(entries[arm]["solved_repetitions"] == REPEATS for arm in ARMS):
            ms = {arm: entries[arm]["median_solved_wall_ns"] / 1e6 for arm in ARMS}
            fully_matched.append({"case_id": name,"expected":one["expected"],
                                  "median_pipeline_ms":ms,
                                  "kissat_over_w030_ratio":ms["kissat"]/ms["w030_prefix_plus_kissat"],
                                  "w027_over_w030_ratio":ms["w027_plus_kissat"]/ms["w030_prefix_plus_kissat"]})

    probes = [p for p in raw["prefix_diagnostics"] if p["stratum"] == "official_external_vlsat2"]
    if len(probes) != 8:
        raise ValueError("missing external source scans")
    certified = [p["case_id"] for p in probes if p["status"] == "UNSAT_CERTIFIED"]
    for p in raw["prefix_diagnostics"]:
        if p["stratum"] == "frozen_adversarial_sat_decoy" and p["status"] != "NO_CERTIFICATE":
            raise ValueError("negative-control false positive")
    if len([p for p in raw["prefix_diagnostics"] if p["stratum"] == "frozen_adversarial_sat_decoy"]) != 4:
        raise ValueError("missing four SAT decoys")

    return {"study": "W-CROSSDOMAIN-032", "analysis": "external_source_verified_censoring_aware",
            "timed_invocations": len(raw["rows"]), "external_case_count": 8,
            "external_arm_outcomes": by_arm,
            "external_prefix_source_proof_cases": certified,
            "external_mean_source_fraction_read": statistics.mean(p["read_clauses"]/p["declared_clauses"] for p in probes),
            "fully_jointly_solved_external_cases": sorted(fully_matched,key=lambda x:x["case_id"]),
            "jointly_solved_case_count": len(fully_matched),
            "scope": "only solved-case pairwise ratios are interpretable as timings; 6s timeouts are right-censored, no inference of a domain-wide solver win"}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m scripts.analyze_w032_external raw-W032.json")
    print(json.dumps(analyze(json.loads(Path(sys.argv[1]).read_text())),indent=2,sort_keys=True))
