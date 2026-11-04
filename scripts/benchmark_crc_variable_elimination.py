"""W-CRC-014: bounded variable elimination rescues chain/ring source #SAT.

Compares default local enumeration (expected budget failure), optional
width-bounded factor variable elimination, PySAT witness search, exact
Fibonacci/Lucas formula, and an independent Ganak model counter.
Connected dense random controls remain explicitly non-admitted.
"""
from __future__ import annotations

import json

from scripts.benchmark_crc_scaling import measured
from scripts.benchmark_crc_highcount import independent_ganak
from scripts.benchmark_crc_adversarial import (
    chain_source, ring_source, planted_random_source, get_source_model,
)
from witnora_core.crc_cutset_count import count_source_by_separator


def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def run(family, n):
    if family == "chain":
        source = chain_source(n)
        left, right = (1,), (n,)
        expected = fibonacci(n + 2)
    elif family == "ring":
        source = ring_source(n)
        left, right = (1,), (n // 2,)
        expected = fibonacci(n - 1) + fibonacci(n + 1)
    elif family == "random":
        source = planted_random_source(n, 13013)
        left, right = (1,), (n,)
        expected = None
    else:
        raise ValueError(family)
    boundary = tuple(range(1, n + 1))
    witness, sat_ms = get_source_model(source, n)
    if witness is None:
        raise AssertionError("expected planted source SAT")

    def count(backend):
        result = count_source_by_separator(
            source, boundary, left, right, witness,
            max_separator_size=2, max_primal_edges=10000,
            max_component_variables=8,
            component_backend=backend,
            max_ve_factor_variables=3,
            max_ve_operations=200000)
        if result is None:
            return None
        return (result.models,
                (result.assignment_states if backend == "enumeration"
                 else result.ve_operations), backend)

    brute = measured(lambda: count("enumeration"), repeats=2, seconds=4)
    exact = measured(lambda: count("variable_elimination"),
                     repeats=2, seconds=4)
    ganak = independent_ganak(source, n, seconds=4)
    if expected is not None and (
        exact["status"] != "EXACT" or exact["models"] != expected):
        raise AssertionError(f"analytic VE contradiction: {family}, n={n}: {exact}")
    if expected is None and exact["status"] == "EXACT":
        # New admissions are allowed only when their integer count
        # independently agrees with the external solver.
        if ganak["status"] != "EXACT":
            raise AssertionError("random exact admission without independent check")
    if ganak["status"] == "EXACT":
        if expected is not None and ganak["models"] != expected:
            raise AssertionError(f"Fibonacci/Lucas-Ganak mismatch: {family}, n={n}")
        if exact["status"] == "EXACT" and ganak["models"] != exact["models"]:
            raise AssertionError(f"Ganak-VE mismatch: {family}, n={n}")

    combined = (round(sat_ms + exact["median_ms"], 4)
                if exact["status"] == "EXACT" else None)
    ratio = (round(combined / ganak["counter_wall_ms"], 3)
             if combined is not None and ganak["status"] == "EXACT"
             and ganak["counter_wall_ms"] else None)
    return {
        "family": family, "n": n, "source_clauses": len(source),
        "analytic_models": expected,
        "old_enumeration": brute, "new_variable_elimination": exact,
        "witness_glucose3_ms": round(sat_ms, 4),
        "combined_witness_and_ve_ms": combined,
        "ganak": ganak, "combined_over_ganak_engine": ratio,
    }


def main():
    rows = []
    for n in (16, 32, 64, 128, 256):
        for family in ("chain", "ring"):
            row = run(family, n)
            rows.append(row)
            print(json.dumps(row, sort_keys=True), flush=True)
    for n in (16, 24, 32):
        row = run("random", n)
        rows.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)
    print(json.dumps({
        "summary": "W-CRC-014 exact width-bounded component VE pilot",
        "cases": len(rows),
        "enumeration_incomplete": sum(
            r["old_enumeration"]["status"] != "EXACT" for r in rows),
        "ve_exact": sum(r["new_variable_elimination"]["status"] == "EXACT"
                        for r in rows),
        "ganak_exact": sum(r["ganak"]["status"] == "EXACT" for r in rows),
        "no_general_sat_speedup_claim": True,
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
