"""Independent native-solver cost gate for Witnora's in-loop masked DPLL.

Run with python-sat installed. Times include solver construction and cleanup.
This compares Python and native C implementations, not like-for-like kernels.
"""
from __future__ import annotations

import json
from statistics import median
from time import perf_counter

from pysat.solvers import Minisat22

from scripts.experiment_event_cached_ood import (
    disconnected_three_sat, mixed_random_parities, random_three_sat,
)
from scripts.benchmark_scaled_minisat_separator import scale_hidden_formula
from scripts.experiment_inloop_masked_state import run_masked


def benchmark(seed_count: int = 8, repeats: int = 5):
    if not 1 <= seed_count <= 24 or not 1 <= repeats <= 20:
        raise ValueError("invalid benchmark budget")
    families = [
        ("hidden", lambda s: scale_hidden_formula(s, 8)),
        ("random_3sat", random_three_sat),
        ("disconnected_3sat", disconnected_three_sat),
        ("mixed_parity", mixed_random_parities),
        ("bridged_parity", lambda s: mixed_random_parities(s, bridge=True)),
    ]
    records = []
    for family, generator in families:
        for seed in range(seed_count):
            formula = generator(seed)
            masked_ms = []
            minisat_ms = []
            for repeat in range(repeats):
                if repeat % 2:
                    order = ("minisat", "masked")
                else:
                    order = ("masked", "minisat")
                outcomes = {}
                for solver in order:
                    start = perf_counter()
                    if solver == "minisat":
                        with Minisat22(bootstrap_with=formula.to_clause_lists()) as sat:
                            answer = sat.solve()
                        minisat_ms.append((perf_counter() - start) * 1000)
                    else:
                        result = run_masked(formula)
                        answer = result["sat"]
                        masked_ms.append((perf_counter() - start) * 1000)
                    outcomes[solver] = answer
                if outcomes["masked"] != outcomes["minisat"]:
                    raise AssertionError((family, seed, "SAT disagreement"))
            records.append({
                "family": family,
                "seed": seed,
                "masked_median_ms": median(masked_ms),
                "minisat_median_ms": median(minisat_ms),
            })

    masked_total = sum(row["masked_median_ms"] for row in records)
    minisat_total = sum(row["minisat_median_ms"] for row in records)
    return {
        "summary": {
            "formulas": len(records),
            "repeats": repeats,
            "answers_agree": len(records),
            "masked_wins": sum(
                row["masked_median_ms"] < row["minisat_median_ms"]
                for row in records
            ),
            "masked_total_ms": round(masked_total, 5),
            "minisat_total_ms": round(minisat_total, 5),
            "masked_to_minisat_time_ratio": round(masked_total / minisat_total, 3),
            "native_solver_advantage_established": False,
        },
        "by_family": [{
            "family": family,
            "masked_ms": round(sum(r["masked_median_ms"] for r in records
                                   if r["family"] == family), 5),
            "minisat_ms": round(sum(r["minisat_median_ms"] for r in records
                                    if r["family"] == family), 5),
        } for family, _ in families],
        "records": records,
    }


if __name__ == "__main__":
    print(json.dumps(benchmark(), sort_keys=True, indent=2))
