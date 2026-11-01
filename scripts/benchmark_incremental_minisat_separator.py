"""One-live-solver separator guidance with reused MiniSat learned clauses.

A cut is used as an assumptions schedule on one MiniSat instance. This
retains the solver between calls, unlike separate residual-component solves.
This is an exploratory algorithmic baseline, not a proof of speed advantage.
"""
from __future__ import annotations

import json
from pathlib import Path
from statistics import median
from time import perf_counter

from pysat.solvers import Minisat22

from witnora_core.cnf import CNFFormula
from witnora_core.autonomous_parity_separator import discover_repaired_separator
from witnora_core.xor import canonical_xor_cnf_clauses, detect_cnf_xor_patterns
from scripts.benchmark_scaled_minisat_separator import scale_hidden_formula


def contradiction_variant(formula):
    """Add parity equation conflicting with a detected equation, same support."""
    equations = sorted(
        detect_cnf_xor_patterns(formula, max_k=6).equations,
        key=lambda eq: (eq.variables, eq.rhs))
    if not equations:
        raise AssertionError("missing parity equation")
    eq = equations[0]
    rows = formula.to_clause_lists()
    rows.extend(canonical_xor_cnf_clauses(eq.variables, 1 - eq.rhs))
    return CNFFormula.from_raw_clauses(rows)


def fresh_solver_answer(rows):
    with Minisat22(bootstrap_with=rows) as solver:
        return solver.solve()


def incremental_cut_answer(rows, cut):
    """Reuse one solver and all learned clauses across boundary assignments."""
    with Minisat22(bootstrap_with=rows) as solver:
        for mask in range(1 << len(cut)):
            assumptions = [
                v if mask & (1 << i) else -v
                for i, v in enumerate(cut)]
            if solver.solve(assumptions=assumptions):
                return True
    return False


def median_time(callback, reps):
    times = []
    result = None
    for _ in range(reps):
        start = perf_counter()
        answer = callback()
        times.append((perf_counter() - start) * 1000)
        if result is None:
            result = answer
        elif result != answer:
            raise AssertionError("answer varied")
    return result, median(times)


def benchmark(seed_count=12, reps=25):
    records = []
    for variant in ("original", "parity_contradiction"):
        for copies in (1, 2, 4, 8):
            for seed in range(seed_count):
                formula = scale_hidden_formula(seed, copies)
                if variant == "parity_contradiction":
                    formula = contradiction_variant(formula)
                rows = formula.to_clause_lists()
                plain_sat, plain_ms = median_time(
                    lambda: fresh_solver_answer(rows), reps)
                started = perf_counter()
                discovery = discover_repaired_separator(formula)
                discovery_ms = (perf_counter() - started) * 1000
                cut = discovery["cut"] if discovery["status"] == "FOUND" else None
                if cut is None:
                    guided_sat, guided_ms = plain_sat, None
                else:
                    guided_sat, guided_ms = median_time(
                        lambda: incremental_cut_answer(rows, cut), reps)
                if guided_sat != plain_sat:
                    raise AssertionError((variant, copies, seed, "SAT mismatch"))
                records.append({
                    "variant": variant, "copies": copies, "seed": seed,
                    "vars": formula.num_vars, "clauses": formula.num_clauses,
                    "sat": plain_sat, "cut": cut,
                    "baseline_ms": round(plain_ms, 6),
                    "guided_cached_ms": (
                        round(guided_ms, 6) if guided_ms is not None else None),
                    "discovery_ms_once": round(discovery_ms, 5),
                    "repetitions": reps,
                })
    detected = [r for r in records if r["cut"] is not None]
    return {
        "summary": {
            "total": len(records),
            "answers_agree": len(records),
            "detected": len(detected),
            "cached_wins": sum(
                r["guided_cached_ms"] < r["baseline_ms"]
                for r in detected),
            "cached_losses_or_ties": sum(
                r["guided_cached_ms"] >= r["baseline_ms"]
                for r in detected),
            "sat_instances": sum(r["sat"] for r in records),
            "unsat_instances": sum(not r["sat"] for r in records),
            "solver": "single incremental PySAT Minisat22",
            "discovery_cost_excluded_from_guided_timings": True,
            "novelty_established": False,
        },
        "records": records,
    }


def main():
    result = benchmark()
    path = Path("research/incremental_minisat_separator_benchmark.json")
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))
    for variant in ("original", "parity_contradiction"):
        for copies in (1, 2, 4, 8):
            selection = [r for r in result["records"]
                         if r["variant"] == variant and r["copies"] == copies
                         and r["cut"] is not None]
            print(json.dumps({
                "variant": variant, "copies": copies,
                "detected": len(selection),
                "baseline_ms": (round(median(r["baseline_ms"]
                                            for r in selection), 6)
                                if selection else None),
                "incremental_ms": (
                    round(median(r["guided_cached_ms"] for r in selection), 6)
                    if selection else None),
            }, sort_keys=True))


if __name__ == "__main__":
    main()
