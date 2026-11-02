"""One-shot frozen holdout for source-subset G5 on larger noisy Tseitin CNFs.

Use no training-seed or result-dependent parameter tuning. Independent SAT
solvers are bounded; a timeout is UNKNOWN, never a proof of hardness or UNSAT.
"""

from __future__ import annotations

import argparse
from itertools import product
import json
from pathlib import Path
from statistics import median

from scripts.experiment_noisy_tseitin_source_subset import (
    bounded_solver, drop_one_xor_clause, make_case, source_subset_candidate,
)

SIZES = (64, 96, 128)
SEEDS = (47, 73)
NOISE_LEVELS = (1, 4)


def median_or_none(values):
    return round(median(values), 6) if values else None


def run(timeout_s: float) -> dict:
    rows = []
    for vertices, seed, noise in product(SIZES, SEEDS, NOISE_LEVELS):
        source = make_case(vertices, seed, noise, odd=True)
        candidate, _, _ = source_subset_candidate(
            source, f"frozen_n{vertices}_seed{seed}_noise{noise}")
        if candidate["status"] != "SOURCE_SUBSET_G5_NATIVE_UNSAT_CANDIDATE":
            raise AssertionError("native contradiction not proved on preregistered holdout")
        baselines = {solver: bounded_solver(source, solver, timeout_s)
                     for solver in ("Minisat22", "Cadical195")}
        if any(row["status"] not in ("UNSAT", "UNKNOWN_TIMEOUT")
               for row in baselines.values()):
            raise AssertionError("contradictory or invalid independent solver result")
        rows.append({
            "vertices": vertices, "seed": seed, "noise_per_vertex": noise,
            "source_sha256": source.formula_hash,
            "variables": len(source.variables), "clauses": len(source.clauses),
            "candidate": candidate,
            "baselines": baselines,
        })
    controls = []
    for name, source in (
        ("sat_even64", make_case(64, 101, 4, odd=False)),
        ("sat_missing_xor_clause64", drop_one_xor_clause(
            make_case(64, 101, 4, odd=True), 64, 101)),
    ):
        candidate, _, _ = source_subset_candidate(source, name)
        independent = bounded_solver(source, "Minisat22", timeout_s)
        if independent["status"] != "SAT":
            raise AssertionError("SAT holdout control was not independently established")
        if candidate["status"] != "DIAGNOSTIC_ONLY":
            raise AssertionError("SAT holdout falsely received native UNSAT")
        controls.append({"name": name, "source_sha256": source.formula_hash,
                         "native_status": candidate["status"],
                         "minisat_status": independent["status"]})
    def worker_times(name):
        return [row["baselines"][name]["worker_ms"] for row in rows
                if row["baselines"][name]["status"] == "UNSAT"]
    def wins(name):
        return sum(row["baselines"][name]["status"] == "UNSAT"
                   and row["candidate"]["elapsed_ms"] < row["baselines"][name]["worker_ms"]
                   for row in rows)
    return {
        "kind": "FROZEN_NOISY_TSEITIN_SOURCE_SUBSET_HOLDOUT",
        "scope": "larger cubic graph Tseitin parity; guarded satisfiability-preserving non-affine clauses",
        "prior_art": "Gaussian elimination on Tseitin XORs is established; this is a falsification benchmark, not an algorithmic invention",
        "limitation": "Native certificate checking only, not per-instance Lean kernel timings or source-text parsing; MiniSat/CaDiCaL are not XOR-specialized baselines",
        "timeout_s": timeout_s, "sizes": list(SIZES), "seeds": list(SEEDS),
        "noise_levels": list(NOISE_LEVELS),
        "rows": rows, "controls": controls,
        "summary": {
            "cases": len(rows),
            "native_g5_certified": sum(r["candidate"]["native_g5_verified"] for r in rows),
            "minisat_unsat": sum(r["baselines"]["Minisat22"]["status"] == "UNSAT" for r in rows),
            "minisat_timeout": sum(r["baselines"]["Minisat22"]["status"] == "UNKNOWN_TIMEOUT" for r in rows),
            "cadical_unsat": sum(r["baselines"]["Cadical195"]["status"] == "UNSAT" for r in rows),
            "cadical_timeout": sum(r["baselines"]["Cadical195"]["status"] == "UNKNOWN_TIMEOUT" for r in rows),
            "native_wins_minisat_worker": wins("Minisat22"),
            "native_wins_cadical_worker": wins("Cadical195"),
            "median_native_ms": median_or_none([r["candidate"]["elapsed_ms"] for r in rows]),
            "median_minisat_solved_worker_ms": median_or_none(worker_times("Minisat22")),
            "median_cadical_solved_worker_ms": median_or_none(worker_times("Cadical195")),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout-s", type=float, default=3.0)
    parser.add_argument("--out", type=Path, default=Path("noisy_tseitin_frozen_holdout.json"))
    args = parser.parse_args()
    if not 0.2 <= args.timeout_s <= 5:
        parser.error("timeout outside safe bounds")
    result = run(args.timeout_s)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
