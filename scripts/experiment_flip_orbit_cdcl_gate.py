"""Does full-CNF-verified sign-flip symmetry reduce real CDCL wall time?

An accepted flip group admits a canonical orbit representative with every
generator pivot bit zero. Adding negative unit clauses for these pivot bits
is SAT-preserving (not pointwise equivalent) if the whole CNF is invariant.
Includes discovery/verification costs in end-to-end timings.
"""
from __future__ import annotations

from statistics import median
from time import perf_counter

from pysat.solvers import Minisat22
from witnora_core.cnf import CNFFormula

from scripts.experiment_verified_flip_orbits import discover, make_case
from scripts.experiment_minisat_first_uip import FirstUIP, pigeonhole


def representative_units(pivots):
    return tuple((-(bit + 1),) for bit in sorted(pivots, reverse=True))


def transformed_clauses(formula, info):
    return (*map(tuple, formula.to_clause_lists()), *representative_units(info["pivots"]))


def solve_once(formula, backend, *, quotient):
    start = perf_counter()
    info = discover(formula, require_source_rows=True) if quotient else None
    clauses = transformed_clauses(formula, info) if quotient else formula.to_clause_lists()
    if backend == "native":
        with Minisat22(bootstrap_with=clauses) as solver:
            sat = solver.solve()
        decisions = None
    elif backend == "python_cdcl":
        solver = FirstUIP(clauses)
        sat = solver.solve(conflict_budget=10000)
        decisions = solver.stats["decisions"]
    else:
        raise ValueError("unknown backend")
    return {"sat": sat, "elapsed_ms": (perf_counter() - start) * 1000,
            "rank": info["rank"] if info else 0, "decisions": decisions}


def benchmark(seeds=5, repeats=5):
    if not 1 <= seeds <= 20 or not 1 <= repeats <= 10:
        raise ValueError("invalid budget")
    cases = []
    for n in (10, 14, 32):
        for seed in range(seeds):
            for kind in ("xor_sat", "xor_unsat", "partially_broken", "random_3sat"):
                cases.append((n, seed, kind, make_case(n, seed, kind)))
    for holes in (3, 4, 5):
        cases.append((holes + 1, holes, "pigeonhole_control",
                      CNFFormula.from_raw_clauses(pigeonhole(holes + 1, holes))))
    rows = []
    for n, seed, family, formula in cases:
        with Minisat22(bootstrap_with=formula.to_clause_lists()) as oracle:
            expected = oracle.solve()
        trials = {mode: [] for mode in ("native", "native_quot", "python", "python_quot")}
        for rep in range(repeats):
            order = ("native", "native_quot", "python", "python_quot")
            order = order[rep % 4:] + order[:rep % 4]
            for mode in order:
                backend = "native" if mode.startswith("native") else "python_cdcl"
                data = solve_once(formula, backend, quotient=mode.endswith("_quot"))
                if data["sat"] != expected:
                    raise AssertionError((family, n, seed, mode, expected, data))
                trials[mode].append(data)
        info = discover(formula, require_source_rows=True)
        rows.append({"family": family, "n": n, "seed": seed,
                     "sat": expected, "verified_rank": info["rank"],
                     **{mode + "_ms": median(v["elapsed_ms"] for v in data)
                        for mode, data in trials.items()},
                     "python_decisions": trials["python"][0]["decisions"],
                     "python_quot_decisions": trials["python_quot"][0]["decisions"]})
    return {"summary": {"cases": len(rows), "all_answers_match": True,
                        "positive_rank_cases": sum(r["verified_rank"] > 0 for r in rows),
                        "native_quot_time_wins": sum(r["native_quot_ms"] < r["native_ms"] for r in rows),
                        "python_quot_time_wins": sum(r["python_quot_ms"] < r["python_ms"] for r in rows),
                        "python_quot_decision_wins": sum(r["python_quot_decisions"] < r["python_decisions"] for r in rows),
                        **{mode + "_total_ms": round(sum(r[mode + "_ms"] for r in rows), 4)
                           for mode in ("native", "native_quot", "python", "python_quot")}},
            "by_family": [{"family": fam,
                           "cases": sum(r["family"] == fam for r in rows),
                           **{mode + "_ms": round(sum(r[mode + "_ms"] for r in rows
                                                      if r["family"] == fam), 4)
                              for mode in ("native", "native_quot", "python", "python_quot")}}
                          for fam in sorted({r["family"] for r in rows})],
            "records": rows}


if __name__ == "__main__":
    import json
    report = benchmark()
    print(json.dumps(report["summary"], indent=2))
    print(json.dumps(report["by_family"], indent=2))
