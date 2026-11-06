"""Preregistered W031 paired-seed clause-order and latency analysis.

Bootstrap resamples 16 independent noise seeds, keeping each matched SAT/
UNSAT pair together; repeats within a seed are summarized by case medians.
No cross-domain performance claim is inferred from a synthetic test family.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path
import random
import statistics
import sys


ORDERS = ("corefirst", "corelast", "shuffled")
ARMS = ("kissat", "w027_plus_kissat", "w030_prefix_plus_kissat")
SEEDS = 16
DRAWS = 5000


def means(draw):
    return [statistics.mean(values[i] for values in draw) for i in range(3)]


def interval(sorted_samples):
    return [sorted_samples[int(len(sorted_samples)*0.025)],
            sorted_samples[min(len(sorted_samples)-1, int(len(sorted_samples)*0.975))]]


def analyze(report):
    if report.get("study") != "W-CROSSDOMAIN-031" or report.get("phase") != "preregistered_order_robustness":
        raise ValueError("only frozen W031 robustness raw data is admissible")
    if report.get("case_count") != SEEDS * len(ORDERS) * 2 + 4:
        raise ValueError("W031 case count incomplete")
    if len(report["rows"]) != report["case_count"] * 3 * len(ARMS):
        raise ValueError("missing timed invocations")
    for r in report["rows"]:
        if r["verdict"] != r["expected"]:
            raise ValueError("wrong or censored source verdict")

    m = {}
    for r in report["per_case_arm_medians"]:
        if r["solved_repetitions"] != 3 or r["timeout_repetitions"]:
            raise ValueError("missing fully solved case")
        m[(r["case_id"],r["arm"])] = r["median_solved_wall_ns"] / 1e6
    p = {r["case_id"]: r for r in report["prefix_diagnostics"]}

    def lookup(name,arm):
        return m[(name,arm)]

    by_order = []
    for order_idx, order in enumerate(ORDERS):
        pair_costs=[]
        proof_read=[]
        for seed in range(SEEDS):
            sat=f"w031_d8192_r{seed}_sat_{order}"
            unsat=f"w031_d8192_r{seed}_unsat_{order}"
            k_sat, k_unsat = lookup(sat,"kissat"),lookup(unsat,"kissat")
            w_sat, w_unsat = lookup(sat,"w030_prefix_plus_kissat"),lookup(unsat,"w030_prefix_plus_kissat")
            old_unsat=lookup(unsat,"w027_plus_kissat")
            pair_costs.append((w_sat-k_sat,k_unsat-w_unsat,old_unsat-w_unsat))
            if p[unsat]["status"] != "UNSAT_CERTIFIED" or p[sat]["status"] != "NO_CERTIFICATE":
                raise ValueError("prefix status contradicts paired family")
            proof_read.append(p[unsat]["read_clauses"] / p[unsat]["declared_clauses"])

        sat_penalty = statistics.mean(x[0] for x in pair_costs)
        unsat_saving = statistics.mean(x[1] for x in pair_costs)
        w027_saving = statistics.mean(x[2] for x in pair_costs)
        rng=random.Random(0x03100310 + order_idx)
        bootstrap=[]
        for _ in range(DRAWS):
            sampled=[pair_costs[rng.randrange(SEEDS)] for _ in range(SEEDS)]
            ave_s,ave_g,ave_old=means(sampled)
            bootstrap.append((ave_s,ave_g,ave_old,(ave_s-ave_g)/2))
        ci_old=interval(sorted(x[2] for x in bootstrap))
        ci_bal=interval(sorted(x[3] for x in bootstrap))
        threshold=sat_penalty/(sat_penalty+unsat_saving) if sat_penalty>0 and unsat_saving>0 else None
        by_order.append({
            "order":order,"matched_seeds":SEEDS,
            "mean_sat_overhead_vs_kissat_ms":sat_penalty,
            "mean_unsat_saving_vs_kissat_ms":unsat_saving,
            "mean_unsat_saving_vs_w027_ms":w027_saving,
            "bootstrap_95pct_ci_for_unsat_saving_vs_w027_ms":ci_old,
            "frozen_H1_w030_beats_w027_on_unsat_at_95pct":ci_old[0]>0,
            "mean_balanced_sat_unsat_extra_vs_kissat_ms":(sat_penalty-unsat_saving)/2,
            "bootstrap_95pct_ci_for_balanced_extra_ms":ci_bal,
            "descriptive_break_even_unsat_fraction":threshold,
            "mean_unsat_source_fraction_read":statistics.mean(proof_read),
            "min_unsat_source_fraction_read":min(proof_read),
            "max_unsat_source_fraction_read":max(proof_read),
            "paired_bootstrap_draws":DRAWS,
        })

    decoys=[k for k in p if k.startswith("decoy_")]
    if len(decoys)!=4 or any(p[k]["status"]!="NO_CERTIFICATE" for k in decoys):
        raise ValueError("lost planted-SAT negative controls")
    return {"study":"W-CROSSDOMAIN-031", "analysis":"preregistered_16_seed_order_robustness",
            "timed_invocations":len(report["rows"]), "independent_noise_seeds":SEEDS,
            "by_order":by_order,"negative_control_sat_decoys":len(decoys),
            "primary_H1":"shuffled UNSAT paired-bootstrap 95% lower bound for mean(W027−W030) >0 ms",
            "primary_H1_passes":next(g for g in by_order if g["order"]=="shuffled")["frozen_H1_w030_beats_w027_on_unsat_at_95pct"],
            "scope":"restricted W026 synthetic generator; bootstrap conditional on its frozen seeds; does not generalize to external SAT instances or P versus NP"}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m scripts.analyze_w031_order raw-W031.json[.gz]")
    path = Path(sys.argv[1])
    # Packaging-only support for archiving the *identical* raw bytes as gzip.
    raw = gzip.open(path, "rt").read() if path.suffix == ".gz" else path.read_text()
    report=json.loads(raw)
    print(json.dumps(analyze(report),indent=2,sort_keys=True))
