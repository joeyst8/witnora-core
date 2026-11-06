"""W029: empirical information limit for a (variables, clauses)-only gate.

This is a post-W027 descriptive audit, NOT a new prespecified benchmark and
not a proof about arbitrary CNFs. The source family is deliberately matched.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
import re
import sys


CASE = re.compile(r"^w026_d(?P<noise>\d+)_r(?P<seed>\d+)_(?P<label>sat|unsat)$")


def audit(report: dict) -> dict:
    if report.get("study") != "W-CROSSDOMAIN-027" or report.get("phase") != "full_preregistered_protocol":
        raise ValueError("requires the frozen W027 full preregistered report")

    rows = {}
    for row in report["rows"]:
        if row["stratum"] == "synthetic_xor" and row["arm"] == "kissat" and row["repeat"] == 0:
            if row["case_id"] in rows:
                raise ValueError("duplicate source metadata for case")
            rows[row["case_id"]] = row

    medians = {}
    for row in report["per_case_arm_medians"]:
        if row["stratum"] == "synthetic_xor":
            medians[(row["case_id"], row["arm"])] = row

    pairs = defaultdict(dict)
    for name, row in rows.items():
        found = CASE.fullmatch(name)
        if found is None:
            raise ValueError(f"unexpected case id: {name}")
        key = (int(found["noise"]), int(found["seed"]))
        label = found["label"].upper()
        if row["expected"] != label:
            raise ValueError("expected label disagrees with case id")
        pairs[key][label] = row

    buckets = defaultdict(list)
    for pair_key, entries in sorted(pairs.items()):
        if set(entries) != {"SAT", "UNSAT"}:
            raise ValueError(f"unmatched SAT/UNSAT case: {pair_key}")
        a, b = entries["SAT"], entries["UNSAT"]
        signature_a = (a["variables"], a["clauses"])
        signature_b = (b["variables"], b["clauses"])
        if signature_a != signature_b:
            raise ValueError(f"header feature mismatch for pair {pair_key}")

        differences = {}
        for label, row in entries.items():
            name = row["case_id"]
            k = medians[(name, "kissat")]
            w = medians[(name, "witnora_plus_kissat")]
            if k["solved_repetitions"] != 3 or w["solved_repetitions"] != 3:
                raise ValueError(f"unusable solved-case median: {name}")
            differences[label] = w["median_solved_wall_ns"] - k["median_solved_wall_ns"]
        buckets[signature_a].append((pair_key, differences))

    groups = []
    for (variables, clauses), items in sorted(buckets.items()):
        sat_overhead = sum(x["SAT"] for _, x in items) / len(items) / 1e6
        unsat_saving = -sum(x["UNSAT"] for _, x in items) / len(items) / 1e6
        # Balanced within each header bucket, so any randomized gate that
        # only knows this pair of counts must activate with identical
        # probability on SAT and UNSAT examples in the bucket.
        gate_on_penalty = (sat_overhead - unsat_saving) / 2
        groups.append({
            "variables": variables,
            "clauses": clauses,
            "matched_pairs": len(items),
            "sat_cases": len(items),
            "unsat_cases": len(items),
            "empirical_sat_probability_conditional_on_header": 0.5,
            "mean_sat_penalty_ms": sat_overhead,
            "mean_unsat_saving_ms": unsat_saving,
            "mean_full_precheck_extra_ms_per_case": gate_on_penalty,
            "best_size_only_gate_on_balanced_W027": "SKIP" if gate_on_penalty > 0 else "RUN" if gate_on_penalty < 0 else "EITHER",
        })

    n = sum(x["matched_pairs"] for x in groups)
    if n == 0:
        raise ValueError("missing paired cases")
    if n * 2 != len(rows):
        raise ValueError("source cases not exhausted by matched pairs")

    return {
        "study": "W-CROSSDOMAIN-029",
        "analysis": "empirical_size_only_gate_information_barrier",
        "source_study": report["study"],
        "source_sha": report["witnora_source_sha"],
        "matched_pair_count": n,
        "header_signature_count": len(groups),
        "all_header_bins_balanced": all(x["sat_cases"] == x["unsat_cases"] for x in groups),
        "all_header_bin_full_precheck_costs_positive": all(x["mean_full_precheck_extra_ms_per_case"] > 0 for x in groups),
        "best_header_only_gate_for_these_empirical_bins": "SKIP_EVERYWHERE" if all(x["mean_full_precheck_extra_ms_per_case"] > 0 for x in groups) else "MIXED_BY_BIN",
        "groups": groups,
        "scope": "Finite frozen synthetic benchmark with paired medians; no universal impossibility for SAT routing and no generalization to unseen real workloads.",
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m scripts.audit_w029_header_gate w027_full_solver_measurements.json")
    print(json.dumps(audit(json.loads(Path(sys.argv[1]).read_text())), indent=2, sort_keys=True))
