"""W-CRC-019: source-solution equivalence versus encoding-sensitive #SAT time.

Controlled negative test: same exact satisfying assignments, alternative
CNF encodings. All count comparisons are on fixed n, no auxiliary vars.
This probes particular counting implementations, not universal complexity.
"""
from __future__ import annotations

import json
import random
import statistics

from scripts.benchmark_crc_matched_semantics import matched_source
from scripts.benchmark_crc_scaling import interaction_density, measured
from scripts.benchmark_crc_highcount import independent_ganak
from witnora_core.crc_source import count_signed_cnf_crc


FAMILIES = {
    "pairwise_forcing": ("base", "shuffled", "entailed_units", "consensus_reduced"),
    "pairwise_parity": ("base", "shuffled", "entailed_wide"),
}


def equivalent_encoding(n: int, family: str, variant: str, seed: int = 19019):
    if family not in FAMILIES or variant not in FAMILIES[family]:
        raise ValueError("unrecognized family/encoding")
    source = list(matched_source(n, family))
    if variant == "base":
        return source
    if variant == "shuffled":
        random.Random(seed + n).shuffle(source)
        return source
    if variant == "entailed_units":
        # Resolution identity: (u|v)&(u|~v) iff u, for each u<v.
        return source + [(u,) for u in range(1, n)]
    if variant == "consensus_reduced":
        # This has the EXACT same S in {0,1}^n as the forcing CNF.
        return [(u,) for u in range(1, n)]
    if variant == "entailed_wide":
        # Each new (a|b|c) clause is implied by existing (a|b).
        extra = []
        for clause in source[:min(12, len(source))]:
            used = {abs(v) for v in clause}
            third = next(v for v in range(1, n + 1) if v not in used)
            extra.append(tuple(clause) + (third,))
        return source + extra
    raise ValueError(variant)


def model_masks(source, n):
    """Independent complete truth-table checker for small n only."""
    if n > 11:
        raise ValueError("model-set enumeration is restricted to n<=11")
    return {
        bits for bits in range(1 << n)
        if all(any(bool(bits & (1 << (abs(lit) - 1))) == (lit > 0)
                   for lit in clause)
               for clause in source)
    }


def run(n: int, family: str, variant: str):
    source = equivalent_encoding(n, family, variant)
    def crc_count():
        result = count_signed_cnf_crc(
            source, n, max_inclusion_subsets=2,
            max_coefficient_states=20000, enable_orbit_oracle=True)
        if result is None:
            return None
        return (result.models, result.extracted_affine_rows,
                result.coefficient_stats.coefficient_backend)
    crc = measured(crc_count, repeats=3, seconds=4)
    independent = [independent_ganak(source, n, seconds=4) for _ in range(3)]
    if any(x["status"] != "EXACT" or x["models"] != 2
           for x in independent):
        raise AssertionError(f"Ganak failed analytic count {n} {family} {variant}: {independent}")
    if crc["status"] == "EXACT" and crc["models"] != 2:
        raise AssertionError(f"CRC wrong on equivalent encoding {n} {family} {variant}: {crc}")
    return {
        "n": n, "family": family, "variant": variant,
        "clauses": len(source),
        "primal_density": interaction_density(source, tuple(range(1, n + 1))),
        "analytic_models": 2,
        "crc": crc,
        "ganak_engine_median_ms": round(statistics.median(
            x["counter_wall_ms"] for x in independent), 4),
        "ganak_engine_range_ms": [
            round(min(x["counter_wall_ms"] for x in independent), 4),
            round(max(x["counter_wall_ms"] for x in independent), 4),
        ],
        "independent_trials": 3,
    }


def main():
    rows = []
    for n in (8, 16, 32, 64):
        for family, variants in FAMILIES.items():
            for variant in variants:
                row = run(n, family, variant)
                rows.append(row)
                print(json.dumps(row, sort_keys=True), flush=True)
    print(json.dumps({
        "summary": "W-CRC-019 equivalent source encodings versus runtime",
        "cases": len(rows),
        "ganak_exact_2_models": len(rows),
        "witnora_exact": sum(r["crc"]["status"] == "EXACT" for r in rows),
        "witnora_incomplete": sum(r["crc"]["status"] != "EXACT" for r in rows),
        "not_a_universal_invariant_impossibility_proof": True,
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
