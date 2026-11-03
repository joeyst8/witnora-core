"""W-CRC-002: bounded scaling/falsification study of overlapping nonlinear CNF.

Independent Glucose3 (PySAT) verifies SAT decisions; its model enumeration
checks small exact counts but is NOT a state-of-the-art #SAT baseline.
Each internal comparison includes source preprocessing, exact states,
timeouts and budget failures. Samples are a pilot, not a solver ranking.

Run:
  python -m pip install python-sat
  python -m scripts.benchmark_crc_scaling
"""
from __future__ import annotations

import argparse
import json
import random
import signal
import statistics
import time
from itertools import combinations

from scripts.benchmark_crc_vs_anf import dense_control, xor_clauses
from witnora_core.anf_structured_counter import count_common_zeros_structured
from witnora_core.crc_source import count_signed_cnf_crc
from witnora_core.violation_image_anf import (
    ANFCountingBudgetExceeded, source_violation_polynomials,
)


class MethodTimeout(TimeoutError):
    pass


def overlapping_parity_source(k: int, seed: int, ratio: float = 4.2):
    """Long exact XOR chain plus dense nonlinear 3-CNF on boundary 1..k."""
    if k < 3:
        raise ValueError("need at least three boundary variables")
    auxiliary = k + 1
    clauses = list(xor_clauses((1, 2, auxiliary), 0))
    for variable in range(3, k):
        nxt = k + variable - 1
        clauses.extend(xor_clauses((auxiliary, variable, nxt), 0))
        auxiliary = nxt
    clauses.extend(xor_clauses((auxiliary, k), 0))
    nvars = 2 * k - 2
    rng = random.Random(seed)
    nonlinear = []
    for _ in range(round(ratio * k)):
        scope = rng.sample(range(1, k + 1), 3)
        nonlinear.append(tuple(v if rng.randrange(2) else -v for v in scope))
    return tuple(clauses + nonlinear), nvars, tuple(nonlinear)


def interaction_density(clauses, boundary):
    """Fraction of pairs in boundary that occur together in a clause."""
    pairs = set()
    bset = set(boundary)
    for clause in clauses:
        scope = sorted(set(abs(lit) for lit in clause) & bset)
        pairs.update(combinations(scope, 2))
    n = len(bset)
    return round(len(pairs) / (n * (n - 1) // 2), 4) if n > 1 else 0.0


def measured(fn, *, repeats: int, seconds: float):
    """Per-method fail-closed wall-clock budget; no partial count accepted."""
    times = []
    value = None
    def alarm(_signum, _frame):
        raise MethodTimeout

    previous = signal.signal(signal.SIGALRM, alarm)
    try:
        for _ in range(repeats):
            start = time.perf_counter()
            try:
                signal.setitimer(signal.ITIMER_REAL, seconds)
                current = fn()
            except MethodTimeout:
                return {"status": "TIMEOUT", "median_ms": None}
            except ANFCountingBudgetExceeded:
                return {"status": "INCOMPLETE_BUDGET", "median_ms": None}
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
            if current is None:
                return {"status": "INCOMPLETE_BUDGET", "median_ms": None}
            times.append((time.perf_counter() - start) * 1000)
            if value is not None and value[0] != current[0]:
                raise AssertionError("nondeterministic exact count")
            value = current
    finally:
        signal.signal(signal.SIGALRM, previous)
    result = {
        "status": "EXACT",
        "median_ms": round(statistics.median(times), 4),
        "models": value[0],
        "states": value[1],
    }
    if len(value) > 2:
        result["backend"] = value[2]
    return result


def independent_pysat(source, nvars, *, max_models, seconds):
    """External SAT decision plus complete enumeration only under a cap."""
    from pysat.solvers import Solver

    def decision():
        with Solver(name="g3", bootstrap_with=source) as solver:
            return (int(solver.solve()), 0)

    sat = measured(decision, repeats=1, seconds=seconds)
    if sat["status"] != "EXACT":
        return sat, {"status": "NOT_CHECKED", "median_ms": None}

    used = {abs(lit) for clause in source for lit in clause}
    free = nvars - len(used)

    def enumeration():
        with Solver(name="g3", bootstrap_with=source) as solver:
            count = 0
            for _ in solver.enum_models():
                count += 1
                if count > max_models:
                    return None
            return (count << free, count)

    counted = measured(enumeration, repeats=1, seconds=seconds)
    if counted["status"] == "INCOMPLETE_BUDGET":
        counted["status"] = "MODEL_CAP_REACHED"
        counted["enumeration_cap"] = max_models
    return sat, counted


def benchmark_case(
    family, source, nvars, nonlinear, boundary, seed,
    *, repeats=2, seconds=2.5, max_states=3000, max_models=1000,
):
    kwargs = dict(repeats=repeats, seconds=seconds)

    def crc_ie():
        result = count_signed_cnf_crc(
            source, nvars, max_spectrum_terms=1024,
            max_inclusion_subsets=1024,
        )
        if result is None:
            return None
        return result.models, result.coefficient_stats.left_fourier_terms

    def crc_shannon():
        result = count_signed_cnf_crc(
            source, nvars, max_spectrum_terms=1024,
            max_inclusion_subsets=1024,
            max_coefficient_states=max_states,
        )
        if result is None:
            return None
        stats = result.coefficient_stats
        return result.models, stats.coefficient_states, stats.coefficient_backend

    def anf():
        polynomials = source_violation_polynomials(source, nvars)
        result = count_common_zeros_structured(
            polynomials, nvars, max_states=max_states,
        )
        return result.satisfying_assignments, result.unique_states

    c = measured(crc_ie, **kwargs)
    s = measured(crc_shannon, **kwargs)
    a = measured(anf, **kwargs)
    external_sat, external_count = independent_pysat(
        source, nvars, max_models=max_models, seconds=seconds,
    )

    known = [r["models"] for r in (c, s, a, external_count)
             if r["status"] == "EXACT"]
    if len(set(known)) > 1:
        raise AssertionError(f"exact model-count disagreement: {known}")
    if external_sat["status"] == "EXACT":
        satisfiable = external_sat["models"] == 1
        if any((models > 0) != satisfiable for models in known):
            raise AssertionError("external SAT decision contradicts count")

    speed = (round(a["median_ms"] / s["median_ms"], 3)
             if a["status"] == s["status"] == "EXACT"
             and s["median_ms"] else None)
    return {
        "family": family,
        "seed": seed,
        "variables": nvars,
        "clauses": len(source),
        "nonlinear_clauses": len(nonlinear),
        "boundary_variables": len(boundary),
        "boundary_interaction_density":
            interaction_density(nonlinear, boundary),
        "crc_ie": c,
        "crc_shannon": s,
        "structured_anf": a,
        "external_pysat_sat_decision": external_sat,
        "external_pysat_model_enumeration": external_count,
        "anf_over_crc_shannon_ratio_if_both_exact": speed,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--seconds", type=float, default=2.5)
    parser.add_argument("--max-states", type=int, default=3000)
    parser.add_argument("--max-models", type=int, default=1000)
    options = parser.parse_args()
    if options.repeats <= 0 or options.seconds <= 0:
        parser.error("positive repeats and seconds required")
    all_rows = []
    for boundary_n in (16, 20, 24):
        for offset in range(3):
            seed = 20261103 + offset
            source, nvars = dense_control(
                seed + boundary_n * 1000, boundary_n,
                round(4.25 * boundary_n),
            )
            all_rows.append(benchmark_case(
                "dense_random_3cnf", source, nvars, source,
                tuple(range(1, boundary_n + 1)), seed,
                repeats=options.repeats, seconds=options.seconds,
                max_states=options.max_states, max_models=options.max_models,
            ))
            source, nvars, nonlinear = overlapping_parity_source(
                boundary_n, seed + boundary_n * 1000,
            )
            all_rows.append(benchmark_case(
                "mixed_xor_dense_3cnf", source, nvars, nonlinear,
                tuple(range(1, boundary_n + 1)), seed,
                repeats=options.repeats, seconds=options.seconds,
                max_states=options.max_states, max_models=options.max_models,
            ))
    for row in all_rows:
        print(json.dumps(row, sort_keys=True), flush=True)
    print(json.dumps({
        "summary": "W-CRC-002",
        "cases": len(all_rows),
        "crc_shannon_exact": sum(
            row["crc_shannon"]["status"] == "EXACT" for row in all_rows),
        "anf_exact": sum(
            row["structured_anf"]["status"] == "EXACT" for row in all_rows),
        "external_count_exact": sum(
            row["external_pysat_model_enumeration"]["status"] == "EXACT"
            for row in all_rows),
        "crc_shannon_faster_when_both_exact": sum(
            row["anf_over_crc_shannon_ratio_if_both_exact"] is not None
            and row["anf_over_crc_shannon_ratio_if_both_exact"] > 1
            for row in all_rows),
        "status": "pilot_only_no_general_sat_claim",
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
