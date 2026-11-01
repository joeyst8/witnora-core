"""Scaling and cached-discovery benchmark against PySAT MiniSat22.

Exploratory synthetic family: independent randomized gadget copies share a
separator. No novel algorithm, no representative industrial SAT workload.
"""
from __future__ import annotations

import json
from pathlib import Path
from statistics import median
from time import perf_counter

from witnora_core.cnf import CNFFormula
from witnora_core.hidden_separator_challenge import make_hidden_separator
from witnora_core.autonomous_parity_separator import discover_repaired_separator
from scripts.benchmark_separator_decomposition import components, simplify


def scale_hidden_formula(seed: int, copies: int) -> CNFFormula:
    if not 1 <= copies <= 8:
        raise ValueError("copies out of range")
    base, info = make_hidden_separator(seed, width=2, cross_noise=False)
    shared = set(info["boundary"])
    variables = [v for v in base.variables if v not in shared]
    rows = []
    for index in range(copies):
        mapping = {v: (v if v in shared else 10000 * (index + 1) + i)
                   for i, v in enumerate(variables, 1)}
        for row in base.to_clause_lists():
            rows.append([mapping[abs(lit)] * (1 if lit > 0 else -1)
                         for lit in row])
    return CNFFormula.from_raw_clauses(rows)


def solve_minisat(rows):
    from pysat.solvers import Minisat22
    with Minisat22(bootstrap_with=rows) as solver:
        return solver.solve()


def solve_minisat_decomposed(rows, cut):
    for mask in range(1 << len(cut)):
        assignment = {v: bool(mask & (1 << i)) for i, v in enumerate(cut)}
        reduced = simplify(rows, assignment)
        if reduced is None:
            continue
        if all(solve_minisat(group) for group in components(reduced)):
            return True
    return False


def timed(call, reps=15):
    elapsed = []
    answer = None
    for _ in range(reps):
        start = perf_counter()
        result = call()
        elapsed.append((perf_counter() - start) * 1000)
        if answer is None:
            answer = result
        elif result != answer:
            raise AssertionError("non-deterministic SAT answer")
    return answer, median(elapsed)


def benchmark(seed_count=4, reps=15):
    records = []
    for copies in (1, 2, 4, 8):
        for seed in range(seed_count):
            formula = scale_hidden_formula(seed, copies)
            rows = formula.to_clause_lists()
            baseline_sat, baseline_ms = timed(
                lambda: solve_minisat(rows), reps)
            discovery_start = perf_counter()
            discovered = discover_repaired_separator(formula)
            discovery_ms = (perf_counter() - discovery_start) * 1000
            cut = discovered["cut"] if discovered["status"] == "FOUND" else None
            if cut is None:
                cached_ms = None
                assisted_sat = baseline_sat
            else:
                assisted_sat, cached_ms = timed(
                    lambda: solve_minisat_decomposed(rows, cut), reps)
            if assisted_sat != baseline_sat:
                raise AssertionError(("solver disagreement", copies, seed))
            records.append({
                "copies": copies, "seed": seed,
                "vars": formula.num_vars, "clauses": formula.num_clauses,
                "sat": baseline_sat, "cut": cut,
                "baseline_minisat_ms_median": round(baseline_ms, 5),
                "cached_decomposition_ms_median": (
                    round(cached_ms, 5) if cached_ms is not None else None),
                "discovery_ms_once": round(discovery_ms, 5),
                "first_use_ms": (
                    round(discovery_ms + cached_ms, 5)
                    if cached_ms is not None else None),
                "reps": reps,
            })
    detected = [r for r in records if r["cut"] is not None]
    return {
        "summary": {
            "total": len(records),
            "answers_agree": len(records),
            "detected": len(detected),
            "cached_wins": sum(
                r["cached_decomposition_ms_median"]
                < r["baseline_minisat_ms_median"] for r in detected),
            "first_use_wins": sum(
                r["first_use_ms"] < r["baseline_minisat_ms_median"]
                for r in detected),
            "solver": "PySAT Minisat22",
            "synthetic_instances_only": True,
            "novelty_established": False,
        },
        "records": records,
    }


def main():
    outcome = benchmark()
    path = Path("research/scaled_minisat_separator_benchmark.json")
    path.write_text(json.dumps(outcome, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    print(json.dumps(outcome["summary"], sort_keys=True))
    for scale in (1, 2, 4, 8):
        sub = [r for r in outcome["records"] if r["copies"] == scale]
        print(json.dumps({
            "copies": scale, "detected": sum(r["cut"] is not None for r in sub),
            "baseline_ms_median": round(median(
                r["baseline_minisat_ms_median"] for r in sub), 5),
            "cached_ms_median": (round(median(
                r["cached_decomposition_ms_median"] for r in sub
                if r["cached_decomposition_ms_median"] is not None), 5)
                if any(r["cut"] is not None for r in sub) else None),
        }, sort_keys=True))


if __name__ == "__main__":
    main()
