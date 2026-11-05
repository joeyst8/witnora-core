"""Reproducible exploratory cycle benchmark; no speed/novelty claims.

Algorithms are Python implementations except the independent PySAT Glucose3
backend. Timing excludes family generation, includes Python XOR extraction
for Witnora, and does NOT include the optional Lean certificate check.
All algorithms run on identical CNF instances. The GF(2) baselines consume
the *known generated XOR edges*, so their input advantage is explicit.
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
import random
from statistics import median
from time import perf_counter

from witnora_core.cnf import CNFFormula
from witnora_core.cycle_discovery import discover_odd_xor_cycle
from witnora_core.xor import canonical_xor_cnf_clauses


def parity_union_find_unsat(edges: list[tuple[int, int, int]]) -> bool:
    """Reference parity DSU, unrelated to Witnora discovery code."""
    parent: dict[int, int] = {}
    rank: dict[int, int] = {}
    parity: dict[int, int] = {}

    def find(x: int) -> tuple[int, int]:
        if x not in parent:
            parent[x], rank[x], parity[x] = x, 0, 0
        if parent[x] == x:
            return x, 0
        root, up = find(parent[x])
        parity[x] ^= up
        parent[x] = root
        return root, parity[x]

    for u, v, rhs in edges:
        ru, pu = find(u)
        rv, pv = find(v)
        if ru == rv:
            if (pu ^ pv) != rhs:
                return True
            continue
        if rank[ru] < rank[rv]:
            ru, rv = rv, ru
            pu, pv = pv, pu
        parent[rv] = ru
        parity[rv] = pu ^ pv ^ rhs
        if rank[ru] == rank[rv]:
            rank[ru] += 1
    return False


def gaussian_gf2_unsat(edges: list[tuple[int, int, int]]) -> bool:
    """Independent integer-bitmask elimination over binary equations."""
    pivots: dict[int, tuple[int, int]] = {}
    for u, v, rhs in edges:
        mask = (1 << (u - 1)) ^ (1 << (v - 1))
        bit = rhs
        while mask:
            pivot = mask.bit_length() - 1
            if pivot not in pivots:
                pivots[pivot] = (mask, bit)
                break
            old_mask, old_rhs = pivots[pivot]
            mask ^= old_mask
            bit ^= old_rhs
        if not mask and bit:
            return True
    return False


def make_case(n: int, kind: str, seed: int) -> tuple[CNFFormula, list[tuple[int, int, int]], bool]:
    if n < 3:
        raise ValueError("n must be at least 3")
    rng = random.Random(seed * 1000003 + n * 31 + sum(map(ord, kind)))
    bits = {v: rng.randrange(2) for v in range(1, n + 1)}
    cycle = [(v, v + 1) for v in range(1, n)] + [(1, n)]
    pairs = list(cycle)
    if "dense" in kind:
        available = sorted(set(combinations(range(1, n + 1), 2)) - set(cycle))
        pairs += rng.sample(available, min(len(available), 2 * n))
    edges = [(u, v, bits[u] ^ bits[v]) for u, v in pairs]
    if kind.startswith("contradictory"):
        u, v, rhs = edges[-1]
        edges[-1] = (u, v, rhs ^ 1)
    clauses: set[tuple[int, ...]] = set()
    for u, v, rhs in edges:
        clauses.update(canonical_xor_cnf_clauses((u, v), rhs))
    if kind == "non_xor_unsat":
        clauses.update(((n + 1,), (-(n + 1),)))
    formula = CNFFormula.from_raw_clauses(sorted(clauses))
    return formula, edges, kind.startswith("contradictory") or kind == "non_xor_unsat"


def measure(action, repeats: int) -> tuple[bool, float]:
    times = []
    outcome = None
    for _ in range(repeats):
        start = perf_counter()
        current = bool(action())
        times.append((perf_counter() - start) * 1000)
        if outcome is not None and current != outcome:
            raise AssertionError("nondeterministic benchmark result")
        outcome = current
    return bool(outcome), median(times)


def benchmark(*, sizes=(8, 24, 64), repeats=3, seed=63063):
    from pysat.solvers import Glucose3
    records = []
    kinds = ("consistent_cycle", "contradictory_cycle",
             "consistent_dense", "contradictory_dense", "non_xor_unsat")
    for n in sizes:
        for kind in kinds:
            formula, edges, expected_unsat = make_case(n, kind, seed)
            clauses = formula.to_clause_lists()

            def glucose_unsat():
                with Glucose3(bootstrap_with=clauses) as solver:
                    return not solver.solve()

            results = {
                "witnora_cycle": measure(
                    lambda: discover_odd_xor_cycle(formula) is not None, repeats),
                "parity_dsu": measure(lambda: parity_union_find_unsat(edges), repeats),
                "gaussian_gf2": measure(lambda: gaussian_gf2_unsat(edges), repeats),
                "glucose3": measure(glucose_unsat, repeats),
            }
            if results["glucose3"][0] != expected_unsat:
                raise AssertionError(f"generated case truth mismatch: {n} {kind}")
            # Specialized XOR methods must agree on edge-induced contradiction,
            # but deliberately cannot decide arbitrary non-XOR clauses.
            xor_unsat = kind.startswith("contradictory")
            for algo in ("witnora_cycle", "parity_dsu", "gaussian_gf2"):
                if results[algo][0] != xor_unsat:
                    raise AssertionError(f"{algo} disagrees with GF2 oracle: {n} {kind}")
            source_digest = sha256(formula.canonical_dimacs().encode("ascii")).hexdigest()
            for algo, (detected, elapsed_ms) in results.items():
                records.append({
                    "seed": seed, "variables": n, "family": kind,
                    "clauses": len(clauses), "xor_edges": len(edges),
                    "source_sha256": source_digest, "algorithm": algo,
                    "detected_unsat": int(detected),
                    "true_unsat": int(expected_unsat),
                    "complete_for_this_cnf": int(detected == expected_unsat),
                    "median_ms": round(elapsed_ms, 6), "repeats": repeats,
                    "lean_checked": 0,
                })
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", type=int, nargs="+", default=[8, 24, 64])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--seed", type=int, default=63063)
    parser.add_argument("--output", type=Path, default=Path("cycle-benchmark.csv"))
    args = parser.parse_args()
    if any(n < 3 for n in args.sizes) or args.repeats < 1:
        parser.error("sizes must be >=3 and repeats must be >=1")
    data = benchmark(sizes=args.sizes, repeats=args.repeats, seed=args.seed)
    with args.output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(data[0]))
        writer.writeheader()
        writer.writerows(data)
    print(json.dumps({
        "records": len(data), "output": str(args.output),
        "algorithms": sorted(set(d["algorithm"] for d in data)),
        "cycle_coverage": [
            {"n": d["variables"], "family": d["family"],
             "detected": bool(d["detected_unsat"]), "truth": bool(d["true_unsat"])}
            for d in data if d["algorithm"] == "witnora_cycle"
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
