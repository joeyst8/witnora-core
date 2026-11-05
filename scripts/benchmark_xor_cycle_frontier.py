"""Cyclic XOR constraint-interaction study with independent CNF proof checks.

Every edge encodes x_u XOR x_v = bit as its *complete* two-clause CNF.
One flipped closing edge frustrates the cycle; added chords are consistent
with a planted assignment. The graph's shortest contradictory cycle is
computed independently of the XOR elimination and proof exporter.
"""

from __future__ import annotations

import argparse
from collections import deque
from hashlib import sha256
import json
import random

from scripts.benchmark_xor_frontier import _external_check, exhaustive_sat
from witnora_core.cnf import CNFFormula
from witnora_core.drat_check import check_drat_text
from witnora_core.drat_trim import find_drat_trim
from witnora_core.xor import XorEquation, canonical_xor_cnf_clauses
from witnora_core.xor_drat import _row_trace_refutation, _sparse_xor_elimination_schedule


def shortest_conflicting_cycle(n: int, edges: list[tuple[int, int]]) -> int:
    """Independent BFS on the graph with the unique flipped edge removed."""
    adjacency = {i: [] for i in range(1, n + 1)}
    for u, v in edges:
        if (u, v) == (1, n):
            continue
        adjacency[u].append(v)
        adjacency[v].append(u)
    queue = deque([(1, 0)])
    seen = {1}
    while queue:
        u, distance = queue.popleft()
        if u == n:
            return distance + 1
        for v in adjacency[u]:
            if v not in seen:
                seen.add(v)
                queue.append((v, distance + 1))
    raise AssertionError("the planted spanning chain must remain connected")


def shortest_odd_parity_cycle(equations: list[XorEquation]) -> list[int] | None:
    """Return source edge indices for a shortest odd-parity cycle.

    BFS visits (vertex, xor-parity) states; no planted assignment or knowledge
    of the flipped edge is used. Only binary, explicitly encoded XOR edges
    belong to this narrow research algorithm. The returned edge subset is
    subsequently checked by independent original-CNF RUP and drat-trim.
    """
    adjacency = {}
    for index, equation in enumerate(equations):
        if len(equation.variables) != 2:
            raise ValueError("odd-cycle witness requires binary XOR edges")
        u, v = equation.variables
        adjacency.setdefault(u, []).append((v, equation.rhs, index))
        adjacency.setdefault(v, []).append((u, equation.rhs, index))
    for neighbors in adjacency.values():
        neighbors.sort()
    best = None
    for start in sorted(adjacency):
        first = (start, 0)
        target = (start, 1)
        parents = {first: None}
        queue = deque([first])
        while queue and target not in parents:
            state = queue.popleft()
            for neighbor, rhs, index in adjacency[state[0]]:
                next_state = (neighbor, state[1] ^ rhs)
                if next_state not in parents:
                    parents[next_state] = (state, index)
                    queue.append(next_state)
        if target not in parents:
            continue
        witness = []
        state = target
        while state != first:
            predecessor, index = parents[state]
            witness.append(index)
            state = predecessor
        witness.reverse()
        canonical = tuple(sorted(witness))
        if best is None or (len(canonical), canonical) < (len(best), tuple(best)):
            best = list(canonical)
    return best


def cycle_case(n: int, *, chords: int = 0, seed: int = 261,
               contradictory: bool = True, variable_gap: int = 1,
               reverse_clauses: bool = False):
    if not 3 <= n <= 80 or not 0 <= chords <= n - 3 or not 1 <= variable_gap <= 1000:
        raise ValueError("cycle case outside bounded research domain")
    rng = random.Random(seed)
    planted = {i: rng.randrange(2) for i in range(1, n + 1)}
    edges = [(i, i + 1) for i in range(1, n)]
    closing = (1, n)
    candidates = [(i, j) for i in range(1, n + 1)
                  for j in range(i + 2, n + 1) if (i, j) != closing]
    rng.shuffle(candidates)
    edges.extend(sorted(candidates[:chords]))
    edges.append(closing)
    equations = []
    for u, v in edges:
        rhs = planted[u] ^ planted[v]
        if (u, v) == closing and contradictory:
            rhs ^= 1
        support = [u * variable_gap, v * variable_gap]
        equations.append(XorEquation(support, rhs,
            source_clauses=canonical_xor_cnf_clauses(support, rhs)))
    clauses = [clause for equation in equations for clause in equation.source_clauses]
    if reverse_clauses:
        clauses.reverse()
    formula = CNFFormula(clauses)
    trace = _sparse_xor_elimination_schedule(equations)["row_operation_trace"]
    return formula, equations, trace, edges, shortest_conflicting_cycle(n, edges)


def measure_cycle(n: int, *, chords: int = 0, seed: int = 261,
                  contradictory: bool = True, variable_gap: int = 1,
                  reverse_clauses: bool = False, compare_rust: bool = False,
                  external_checker: str | None = None,
                  max_proof_clauses: int = 20000, max_proof_bytes: int = 500000):
    formula, equations, trace, edges, shortest = cycle_case(n, chords=chords,
        seed=seed, contradictory=contradictory, variable_gap=variable_gap,
        reverse_clauses=reverse_clauses)
    opts = dict(max_proof_clauses=max_proof_clauses,
                max_proof_bytes=max_proof_bytes, timeout_seconds=15)
    proof, error, stats = _row_trace_refutation(formula, equations, trace,
                                               backend="python", **opts)
    if compare_rust:
        native = _row_trace_refutation(formula, equations, trace,
                                       backend="rust", **opts)
        if native != (proof, error, stats):
            raise AssertionError(f"cycle n={n}, chords={chords} native mismatch")
    witness_indices = shortest_odd_parity_cycle(equations)
    if contradictory:
        if witness_indices is None or len(witness_indices) != shortest:
            raise AssertionError("independent shortest inconsistent cycle disagrees")
        witness_equations = [equations[index] for index in witness_indices]
        witness_trace = _sparse_xor_elimination_schedule(witness_equations)["row_operation_trace"]
        compact, compact_error, compact_stats = _row_trace_refutation(
            formula, witness_equations, witness_trace, backend="python", **opts)
        if compare_rust:
            native_compact = _row_trace_refutation(
                formula, witness_equations, witness_trace, backend="rust", **opts)
            if native_compact != (compact, compact_error, compact_stats):
                raise AssertionError("native compact-cycle candidate disagreement")
        if compact_error is not None or not compact or not check_drat_text(formula, compact)["verified"]:
            raise AssertionError(f"compact odd-cycle proof rejected: {compact_error}")
        if external_checker is not None and not _external_check(formula, compact, external_checker):
            raise AssertionError("external drat-trim rejected compact cycle proof")
    else:
        if witness_indices is not None:
            raise AssertionError("SAT parity graph cannot have an odd XOR cycle")
        compact_stats = {"proof_clause_count_actual": 0, "proof_file_size_bytes": 0}
    if contradictory and error is None:
        if not proof or not check_drat_text(formula, proof)["verified"]:
            raise AssertionError("contradictory cyclic XOR proof failed original-CNF RUP")
        if external_checker is not None and not _external_check(formula, proof, external_checker):
            raise AssertionError("external drat-trim rejected cyclic XOR proof")
    elif not contradictory and (proof is not None or error != "ROW_OPERATION_TRACE_DID_NOT_DERIVE_EMPTY"):
        raise AssertionError("SAT graph emitted UNSAT proof or wrong status")
    return {"n": n, "chords": chords, "seed": seed,
            "contradictory": contradictory,
            "graph_cycle_rank": len(edges) - n + 1,
            "shortest_inconsistent_cycle_edges": shortest if contradictory else None,
            "source_clauses": formula.num_clauses,
            "trace_operations": len(trace),
            "proof_clauses": stats["proof_clause_count_actual"],
            "proof_bytes": stats["proof_file_size_bytes"],
            "shortest_witness_edges": len(witness_indices) if witness_indices else None,
            "witness_proof_clauses": compact_stats["proof_clause_count_actual"],
            "witness_proof_bytes": compact_stats["proof_file_size_bytes"],
            "status": "CANDIDATE_RUP_ACCEPTED" if proof else error,
            "original_cnf_sha256": sha256(formula.canonical_dimacs().encode()).hexdigest(),
            "proof_sha256": sha256(proof.encode()).hexdigest() if proof else None,
            "external_drat_verified": bool(proof and external_checker is not None),
            "native_differential": compare_rust}


def run_cycles(*, compare_rust: bool = False,
               external_checker: str | None = None):
    if external_checker is not None:
        external_checker = find_drat_trim(external_checker)
        if external_checker is None:
            raise ValueError("requested external drat-trim unavailable")
    configs = ((3, 0), (4, 0), (5, 1), (6, 1), (8, 2),
               (10, 3), (12, 4), (16, 5), (20, 6), (40, 10))
    rows = [measure_cycle(n, chords=chords, seed=261000+n,
                          compare_rust=compare_rust, external_checker=external_checker)
            for n, chords in configs]
    return {"status": "BOUNDED_CONSTRAINT_INTERACTION_STUDY_NOT_GENERAL_THEOREM",
            "external_drat_verification_performed": external_checker is not None,
            "native_differential_performed": compare_rust, "rows": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compare-rust", action="store_true")
    parser.add_argument("--drat-trim")
    args = parser.parse_args()
    print(json.dumps(run_cycles(compare_rust=args.compare_rust,
        external_checker=args.drat_trim), sort_keys=True))


if __name__ == "__main__":
    main()
