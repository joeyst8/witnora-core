"""Held-out cycle-witness optimality oracle and native/external proof checks.

The exhaustive oracle enumerates edge subsets rather than using parity-state
BFS. It is deliberately capped and independent of the witness algorithm.
"""

from __future__ import annotations

import argparse
from itertools import combinations
import json
import random

from scripts.benchmark_xor_cycle_frontier import (
    cycle_case, measure_cycle, shortest_odd_parity_cycle,
)
from scripts.benchmark_xor_frontier import exhaustive_sat
from witnora_core.drat_trim import find_drat_trim


def exhaustive_shortest_odd_cycle(equations, *, max_edges: int = 13) -> int | None:
    """Independent exhaustive simple-cycle subset checker, at most 13 edges."""
    if len(equations) > max_edges:
        raise ValueError("exhaustive cycle oracle edge cap exceeded")
    graph = []
    for equation in equations:
        if len(equation.variables) != 2:
            raise ValueError("cycle oracle accepts only binary XOR equations")
        u, v = equation.variables
        graph.append((u, v, equation.rhs))
    for size in range(3, len(graph) + 1):
        for subset in combinations(range(len(graph)), size):
            degrees = {}
            parity = 0
            neighbors = {}
            for index in subset:
                u, v, rhs = graph[index]
                parity ^= rhs
                degrees[u] = degrees.get(u, 0) + 1
                degrees[v] = degrees.get(v, 0) + 1
                neighbors.setdefault(u, set()).add(v)
                neighbors.setdefault(v, set()).add(u)
            if parity != 1 or len(degrees) != size or any(d != 2 for d in degrees.values()):
                continue
            start = next(iter(degrees))
            seen, frontier = {start}, [start]
            while frontier:
                current = frontier.pop()
                for neighbor in neighbors[current]:
                    if neighbor not in seen:
                        seen.add(neighbor)
                        frontier.append(neighbor)
            if len(seen) == size:
                return size
    return None


def run_heldout(*, samples: int = 72, compare_rust: bool = False,
                external_checker: str | None = None):
    if not 1 <= samples <= 200:
        raise ValueError("held-out sample count outside bounded domain")
    if external_checker is not None:
        external_checker = find_drat_trim(external_checker)
        if external_checker is None:
            raise ValueError("requested external checker unavailable")
    rng = random.Random(281299)
    records = []
    for trial in range(samples):
        n = rng.randrange(3, 9)
        chords = rng.randrange(0, min(n - 3, 4) + 1)
        seed = rng.randrange(1, 1_000_000)
        formula, equations, _, _, _ = cycle_case(n, chords=chords, seed=seed)
        bfs = shortest_odd_parity_cycle(equations)
        brute_force_length = exhaustive_shortest_odd_cycle(equations)
        if bfs is None or len(bfs) != brute_force_length:
            raise AssertionError(f"held-out shortest-cycle oracle disagreement trial {trial}")
        if exhaustive_sat(formula):
            raise AssertionError("original-CNF inconsistent cycle was SAT")
        result = measure_cycle(n, chords=chords, seed=seed,
            compare_rust=compare_rust, external_checker=external_checker)
        if result["status"] != "CANDIDATE_RUP_ACCEPTED":
            raise AssertionError("held-out proof candidate not accepted")
        if trial % 3 == 0:
            sat_formula, sat_equations, _, _, _ = cycle_case(n, chords=chords,
                seed=seed, contradictory=False)
            if not exhaustive_sat(sat_formula) or shortest_odd_parity_cycle(sat_equations) is not None:
                raise AssertionError("SAT graph control failed independent checks")
        records.append({"trial": trial, "n": n, "chords": chords, "seed": seed,
            "shortest_odd_cycle": len(bfs),
            "brute_force_odd_cycle": brute_force_length,
            "full_proof_clauses": result["proof_clauses"],
            "witness_proof_clauses": result["witness_proof_clauses"],
            "cnf_sha256": result["original_cnf_sha256"],
            "external_drat_verified": result["external_drat_verified"]})
    return {"status": "BOUNDED_HELDOUT_WITNESS_ORACLE_PASSED_NOT_COMPLEXITY_CLAIM",
            "sample_count": len(records),
            "sat_control_count": sum(index % 3 == 0 for index in range(samples)),
            "strict_witness_improvements": sum(row["witness_proof_clauses"] < row["full_proof_clauses"]
                                               for row in records),
            "native_differential": compare_rust,
            "external_drat_verification_performed": external_checker is not None,
            "records": records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=72)
    parser.add_argument("--compare-rust", action="store_true")
    parser.add_argument("--drat-trim")
    args = parser.parse_args()
    result = run_heldout(samples=args.samples, compare_rust=args.compare_rust,
                         external_checker=args.drat_trim)
    print(json.dumps({k:v for k,v in result.items() if k!="records"}, sort_keys=True))


if __name__ == "__main__":
    main()
