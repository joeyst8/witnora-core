"""Cost-aware paired W027 analysis, prespecified before full run completed.

Only evaluates costs of the source-XOR synthetic family. A break-even
UNSAT prevalence in this distribution is not an empirical prevalence
estimate for real-world CNFs and does not establish a solver win.
"""

from __future__ import annotations

import json
from pathlib import Path
import random
import statistics
import sys


NOISE_LEVELS = (0, 32, 256, 1024, 4096, 8192)
REPLICATES = 16
BOOTSTRAP_DRAWS = 5000


def break_even(sat_penalty_ns, unsat_saving_ns):
    """Witnora faster if (1-p)*SAT_penalty - p*UNSAT_saving < 0.

    Returns a textual inequality; positive costs usually yield p > t.
    """
    denom = sat_penalty_ns + unsat_saving_ns
    if abs(denom) < 1e-9:
        return {"rule": "always" if sat_penalty_ns < 0 else "never", "threshold": None}
    bound = sat_penalty_ns / denom
    if denom > 0:
        if bound <= 0:
            return {"rule": "always", "threshold": None}
        if bound >= 1:
            return {"rule": "never", "threshold": None}
        return {"rule": "UNSAT_fraction_gt", "threshold": bound}
    if bound <= 0:
        return {"rule": "never", "threshold": None}
    if bound >= 1:
        return {"rule": "always", "threshold": None}
    return {"rule": "UNSAT_fraction_lt", "threshold": bound}


def analyze(report):
    if report["study"] != "W-CROSSDOMAIN-027" or report["phase"] != "full_preregistered_protocol":
        raise ValueError("not a full W027 results file")
    by_case = {}
    for row in report["per_case_arm_medians"]:
        by_case.setdefault(row["case_id"], {})[row["arm"]] = row

    def paired_median(case):
        a = by_case[case]["kissat"]
        b = by_case[case]["witnora_plus_kissat"]
        if a["solved_repetitions"] != 3 or b["solved_repetitions"] != 3:
            return None
        return a["median_solved_wall_ns"], b["median_solved_wall_ns"]

    outcome = []
    for noise in NOISE_LEVELS:
        paired = []
        for replicate in range(REPLICATES):
            sat = paired_median(f"w026_d{noise}_r{replicate}_sat")
            unsat = paired_median(f"w026_d{noise}_r{replicate}_unsat")
            if sat is None or unsat is None:
                continue
            paired.append((sat[1] - sat[0], unsat[0] - unsat[1]))

        if not paired:
            outcome.append({"noise": noise, "usable_matched_pairs": 0,
                            "unusable_matched_pairs": REPLICATES, "break_even": None})
            continue
        p_sat = statistics.mean(x[0] for x in paired)
        g_unsat = statistics.mean(x[1] for x in paired)
        decision = break_even(p_sat, g_unsat)
        rng = random.Random(0x02702700 + noise)
        thresholds = []
        for _ in range(BOOTSTRAP_DRAWS):
            bootstrap = [paired[rng.randrange(len(paired))] for _ in paired]
            s = statistics.mean(x[0] for x in bootstrap)
            g = statistics.mean(x[1] for x in bootstrap)
            bound = break_even(s, g)
            if bound["rule"] == "UNSAT_fraction_gt":
                thresholds.append(bound["threshold"])
        thresholds.sort()
        ci = [thresholds[int(0.025 * len(thresholds))],
              thresholds[min(len(thresholds) - 1, int(0.975 * len(thresholds)))]] if thresholds else None
        outcome.append({"noise": noise, "usable_matched_pairs": len(paired),
                        "unusable_matched_pairs": REPLICATES - len(paired),
                        "mean_sat_overhead_ms": p_sat / 1e6,
                        "mean_unsat_saving_ms": g_unsat / 1e6,
                        "break_even": decision,
                        "conditional_bootstrap_95pct_interval": ci,
                        "bootstrap_intervals_only_for_gt_cases": len(thresholds),
                        "bootstrap_draws": BOOTSTRAP_DRAWS})
    return {"study": "W-CROSSDOMAIN-027", "analysis": "synthetic_matched_break_even",
            "note": "Exploratory within frozen W026 synthetic family; no assumed real UNSAT prevalence; bootstrap intervals exclude non-gt regimes and are conditional",
            "noise_groups": outcome}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m scripts.analyze_w027_break_even raw-full-w027.json")
    report = json.loads(Path(sys.argv[1]).read_text())
    print(json.dumps(analyze(report), indent=2, sort_keys=True))
