"""W-CRC-004: exact orbit-cardinality coefficient extraction pilot.

Dense r=3 CNFs containing every signed triple except <=3 omissions.
This is a known lifted cardinality family. The benchmark includes
source-to-count costs, a Shannon fallback control, and independent Ganak
integer counting. It does not establish general-CNF complexity bounds.
"""
from __future__ import annotations

import json
import statistics
from itertools import combinations
from math import comb

from scripts.benchmark_crc_highcount import independent_ganak
from scripts.benchmark_crc_scaling import measured
from scripts.benchmark_crc_vs_anf import xor_clauses
from witnora_core.crc_source import count_signed_cnf_crc


def uniform_clauses(n: int, *, missing: int = 0):
    """Complete all-positive 3-uniform CNF with first d supports removed."""
    triples = list(combinations(range(1, n + 1), 3))
    if missing < 0 or missing > 3:
        raise ValueError("defects must be in 0..3")
    clauses = tuple(triples[missing:])
    return clauses, 1 + n + comb(n, 2) + missing


def coupled_parity(source, k):
    """Canonical XOR-CNF chain forcing odd parity on the k source bits."""
    if k < 3:
        raise ValueError("need k >= 3")
    previous = k + 1
    chain = list(xor_clauses((1, 2, previous), 0))
    for variable in range(3, k):
        nxt = k + variable - 1
        chain.extend(xor_clauses((previous, variable, nxt), 0))
        previous = nxt
    chain.extend(xor_clauses((previous, k), 1))
    return tuple(chain) + tuple(source), 2 * k - 2


def compare(source, nvars, expected, *, seconds=3):
    def orbit():
        result = count_signed_cnf_crc(
            source, nvars, max_spectrum_terms=1024,
            max_inclusion_subsets=1024, enable_orbit_oracle=True,
        )
        if result is None:
            return None
        return (result.models, result.coefficient_stats.coefficient_states,
                result.coefficient_stats.coefficient_backend)

    def shannon():
        result = count_signed_cnf_crc(
            source, nvars, max_spectrum_terms=1024,
            max_inclusion_subsets=1024, max_coefficient_states=3000,
        )
        if result is None:
            return None
        return (result.models, result.coefficient_stats.coefficient_states,
                result.coefficient_stats.coefficient_backend)

    o = measured(orbit, repeats=2, seconds=seconds)
    s = measured(shannon, repeats=1, seconds=seconds)
    g = independent_ganak(source, nvars, seconds=seconds)
    for method in (o, s, g):
        if method["status"] == "EXACT" and method["models"] != expected:
            raise AssertionError(
                f"exact count disagrees with independent construction: {method}"
            )
    return {"expected_models": expected,
            "orbit": o, "shannon": s, "ganak": g,
            "orbit_faster_than_ganak_engine": (
                round(g["counter_wall_ms"] / o["median_ms"], 3)
                if o["status"] == g["status"] == "EXACT" and o["median_ms"]
                else None)}


def main():
    results = []
    for k, defects in ((12, 0), (20, 2), (28, 2), (36, 3)):
        right, count = uniform_clauses(k, missing=defects)
        results.append({
            "family": "uniform_dense_nonlinear",
            "boundary_variables": k,
            "source_variables": k,
            "source_clauses": len(right),
            "missing_triples": defects,
            **compare(right, k, count),
        })
        mixed, nvars = coupled_parity(right, k)
        # For even k, odd global parity allows one or three false bits.
        odd_count = k + defects
        results.append({
            "family": "uniform_dense_with_global_parity",
            "boundary_variables": k,
            "source_variables": nvars,
            "source_clauses": len(mixed),
            "missing_triples": defects,
            **compare(mixed, nvars, odd_count),
        })
    for result in results:
        print(json.dumps(result, sort_keys=True), flush=True)
    ratios = [x["orbit_faster_than_ganak_engine"] for x in results
              if x["orbit_faster_than_ganak_engine"] is not None]
    print(json.dumps({
        "summary": "W-CRC-004",
        "cases": len(results),
        "orbit_exact": sum(x["orbit"]["status"] == "EXACT" for x in results),
        "ganak_exact": sum(x["ganak"]["status"] == "EXACT" for x in results),
        "shannon_exact": sum(x["shannon"]["status"] == "EXACT" for x in results),
        "median_ganak_orbit_ratio_if_both_exact": (
            round(statistics.median(ratios), 3) if ratios else None),
        "claim": "known_lifted_cardinality_not_general_sat",
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
