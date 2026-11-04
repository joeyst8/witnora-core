"""W-CRC-018: match K_n, clause count, and model count; probe semantics.

These are deliberately simple known classes. Their uniform solution
distributions have different backbone/pairwise interaction profiles,
though both have precisely two models. A separate triple-XOR example
demonstrates why pairwise dependence cannot detect all interactions.
"""
from __future__ import annotations

from itertools import combinations, product
import json
import random

from scripts.benchmark_crc_dense_semantics import dense_source
from scripts.benchmark_crc_scaling import interaction_density, measured
from scripts.benchmark_crc_highcount import independent_ganak
from witnora_core.crc_source import count_signed_cnf_crc


def matched_source(n: int, family: str, seed: int = 17017):
    if n < 3:
        raise ValueError("at least three variables needed")
    if family == "pairwise_parity":
        return dense_source(n, "parity_consistent", seed)
    if family == "pairwise_forcing":
        # For each u<v: (u OR v) AND (u OR not v) iff u.
        # All 1..n-1 forced true; variable n free: exactly TWO models.
        return [clause for u, v in combinations(range(1, n + 1), 2)
                for clause in ((u, v), (u, -v))]
    raise ValueError(family)


def triple_parity_source(rhs: int = 0):
    """CNF encoding exactly x1 XOR x2 XOR x3 = rhs."""
    return [(1 if a == 0 else -1,
             2 if b == 0 else -2,
             3 if c == 0 else -3)
            for a, b, c in product((0, 1), repeat=3)
            if (a ^ b ^ c) != rhs]


def semantic_profile(source, n: int):
    """Enumerate solutions and test pairwise independence exactly.

    Counts N_ab are projected counts of complete assignments.
    Pair dependence iff N00*N11 - N01*N10 != 0, when satisfiable.
    O(2^n * (clauses + n^2)): an exact SMALL-n diagnostic, NOT a
    scalable source certificate or a proposed #SAT algorithm.
    """
    if not 0 <= n <= 14:
        raise ValueError("diagnostic intentionally capped at n<=14")
    source = tuple(tuple(clause) for clause in source)
    solutions = []
    for bits in range(1 << n):
        if all(any(bool(bits & (1 << (abs(lit) - 1))) == (lit > 0)
                   for lit in clause)
               for clause in source):
            solutions.append(bits)
    count = len(solutions)
    if not count:
        return {"models": 0, "status": "UNSAT_NO_DISTRIBUTION"}
    ones = [sum(bool(bits & (1 << v)) for bits in solutions)
            for v in range(n)]
    live = [v + 1 for v, one in enumerate(ones) if 0 < one < count]
    dependencies = []
    for u, v in combinations(range(n), 2):
        cells = [0, 0, 0, 0]
        for bits in solutions:
            cells[(int(bool(bits & (1 << u))) << 1) |
                  int(bool(bits & (1 << v)))] += 1
        if cells[0] * cells[3] != cells[1] * cells[2]:
            dependencies.append((u + 1, v + 1))
    triple_coefficient = sum(
        -1 if ((bits & 1) ^ ((bits >> 1) & 1) ^
               ((bits >> 2) & 1)) else 1
        for bits in solutions
    ) if n >= 3 else None
    return {
        "status": "EXACT_SMALL_ENUM",
        "models": count,
        "backbone_variables": n - len(live),
        "live_variables": len(live),
        "pairwise_dependent_edges": len(dependencies),
        "dependency_pairs": dependencies,
        "triple_123_walsh_sum": triple_coefficient,
    }


def run(n: int, family: str):
    source = matched_source(n, family)
    expected_clauses = n * (n - 1)
    assert len(source) == expected_clauses
    assert interaction_density(source, tuple(range(1, n + 1))) == 1.0
    expected_live = n if family == "pairwise_parity" else 1
    expected_pairs = n * (n - 1) // 2 if family == "pairwise_parity" else 0
    profile = semantic_profile(source, n) if n <= 12 else None
    if profile is not None:
        assert profile["models"] == 2
        assert profile["live_variables"] == expected_live
        assert profile["pairwise_dependent_edges"] == expected_pairs
    def crc():
        result = count_signed_cnf_crc(
            source, n, max_inclusion_subsets=2,
            max_coefficient_states=20000, enable_orbit_oracle=True)
        if result is None:
            return None
        return (result.models, result.extracted_affine_rows,
                result.coefficient_stats.coefficient_backend)
    got = measured(crc, repeats=2, seconds=4)
    ganak = independent_ganak(source, n, seconds=4)
    if ganak["status"] != "EXACT" or ganak["models"] != 2:
        raise AssertionError(f"independent Ganak count failed: {family},n={n}, {ganak}")
    if got["status"] == "EXACT" and got["models"] != 2:
        raise AssertionError(f"Witnora mismatch: {family},n={n}, {got}")
    if family == "pairwise_parity" and got["status"] != "EXACT":
        raise AssertionError(f"known affine family incomplete: n={n}, {got}")
    return {
        "n": n, "family": family,
        "primal_edges": n * (n - 1) // 2,
        "source_clauses": len(source), "analytic_models": 2,
        "predicted_live_variables": expected_live,
        "predicted_pairwise_dependent_edges": expected_pairs,
        "small_exact_semantic_profile": profile,
        "witnora_crc": got, "ganak": ganak,
    }


def main():
    rows = []
    for n in (8, 12, 16, 32, 64):
        for family in ("pairwise_parity", "pairwise_forcing"):
            row = run(n, family)
            rows.append(row)
            print(json.dumps(row, sort_keys=True), flush=True)
    triple = semantic_profile(triple_parity_source(), 3)
    assert (triple["models"] == 4 and triple["live_variables"] == 3
            and triple["pairwise_dependent_edges"] == 0
            and abs(triple["triple_123_walsh_sum"]) == 4)
    print(json.dumps({"counterexample": "three_way_xor_hidden_from_pairwise",
                      "semantic_profile": triple}, sort_keys=True), flush=True)
    print(json.dumps({
        "summary": "W-CRC-018 matched graph, clauses and model count",
        "cases": len(rows),
        "ganak_exact": sum(x["ganak"]["status"] == "EXACT" for x in rows),
        "witnora_exact": sum(x["witnora_crc"]["status"] == "EXACT" for x in rows),
        "small_semantic_profiles": sum(x["small_exact_semantic_profile"] is not None
                                       for x in rows),
        "pairwise_blind_spot_confirmed": True,
        "no_new_complexity_theorem": True,
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
