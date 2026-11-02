"""Check whether selective same-support pair screening adds anything to exact XOR detection.

The detected rows are *implied* by the original CNF, and the only clauses
eligible for screening on a detected support are the complete XOR encoding
itself. Thus a consistent set of detected rows already satisfies each such
pair. This is a structural negative control, not a solver acceleration.
"""
from __future__ import annotations

from statistics import median
from time import perf_counter

from pysat.solvers import Minisat22

from witnora_core.cnf import CNFFormula
from witnora_core.xor import canonical_xor_cnf_clauses, detect_cnf_xor_patterns
from scripts.experiment_affine_pair_conflict import selective_screen_pairs
from scripts.experiment_affine_dimension_diagnostic import gf2_dimension
from scripts.experiment_inloop_masked_state import run_masked


def source_bound_screen(formula):
    detected = detect_cnf_xor_patterns(formula, max_k=3)
    rows = tuple((sum(1 << (v - 1) for v in eq.variables), eq.rhs)
                 for eq in detected.equations
                 if eq.safe_use and eq.exact_full_encoding)
    result = selective_screen_pairs(formula.max_var, rows, formula.to_clause_lists())
    return result, rows


def instance(n, seed, kind):
    """Two interlinked exact XOR patterns, with optional contradictory parity."""
    from random import Random
    rng = Random(seed + n * 1000)
    a, b, c = rng.sample(range(1, n + 1), 3)
    d = next(v for v in range(1, n + 1) if v not in (a, b, c))
    support = (a, b, c)
    clauses = list(canonical_xor_cnf_clauses(support, 0))
    clauses.extend(canonical_xor_cnf_clauses((b, c, d), seed % 2))
    if kind == "blocked":
        # Restrict all assignments of a via units after the XOR constraints.
        clauses.extend([(a,), (-a,)])
    elif kind == "random":
        for _ in range(n):
            vs = rng.sample(range(1, n + 1), 3)
            clauses.append(tuple(v if rng.randrange(2) else -v for v in vs))
    return CNFFormula.from_raw_clauses(clauses)


def run(seeds=8, repeats=3):
    records = []
    for n in (16, 32):
        for seed in range(seeds):
            for kind in ("xor_only", "blocked", "random"):
                formula = instance(n, seed, kind)
                screen, rows = source_bound_screen(formula)
                assert rows, "fixture must contain source-bound XOR rows"
                consistent = gf2_dimension(formula.max_var, rows) is not None
                # The pair detector has no independent contradictory witness.
                assert consistent and screen["status"] == "UNKNOWN", (n, seed, kind, screen)
                with Minisat22(bootstrap_with=formula.to_clause_lists()) as solver:
                    expected = solver.solve()
                baseline = [run_masked(formula) for _ in range(repeats)]
                assert all(r["sat"] == expected for r in baseline)
                timed = []
                for _ in range(repeats):
                    t = perf_counter()
                    source_bound_screen(formula)
                    run_masked(formula)
                    timed.append((perf_counter() - t) * 1000)
                records.append({"n": n, "seed": seed, "kind": kind,
                                "detected_rows": len(rows), "sat": expected,
                                "screen_status": screen["status"],
                                "pairs_checked": screen["pairs_checked"],
                                "baseline_ms": median(r["elapsed_ms"] for r in baseline),
                                "with_precheck_ms": median(timed)})
    return {"summary": {
        "cases": len(records),
        "source_bound_pair_conflicts": sum(r["screen_status"] == "UNSAT" for r in records),
        "pairs_checked": sum(r["pairs_checked"] for r in records),
        "baseline_total_ms": round(sum(r["baseline_ms"] for r in records), 4),
        "precheck_total_ms": round(sum(r["with_precheck_ms"] for r in records), 4),
        "precheck_time_wins": sum(r["with_precheck_ms"] < r["baseline_ms"] for r in records),
        "note": "precheck only once, not at every search node; intentionally favorable cost bound",
    }, "records": records}


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2))
