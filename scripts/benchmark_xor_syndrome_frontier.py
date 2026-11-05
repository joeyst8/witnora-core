"""Bounded shortest contradictory GF(2) subsystem research prototype.

Dynamic programming tracks reachable (XOR support, RHS) syndromes and retains
the smallest source-row subset per state. This is exact within its declared
finite caps, but can take exponential space in GF(2) rank. Candidate DRAT
proofs require the unchanged original-CNF independent checker.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
from itertools import combinations
import json
import random

from scripts.benchmark_xor_frontier import _external_check, exhaustive_sat
from witnora_core.cnf import CNFFormula
from witnora_core.drat_check import check_drat_text
from witnora_core.drat_trim import find_drat_trim
from witnora_core.xor import XorEquation, canonical_xor_cnf_clauses
from witnora_core.xor_drat import _row_trace_refutation, _sparse_xor_elimination_schedule


def _masks(equations: list[XorEquation], *, max_variables: int = 16):
    variables = sorted({v for eq in equations for v in eq.variables})
    if len(variables) > max_variables:
        raise ValueError("GF2 syndrome variable cap exceeded")
    positions = {v: i for i, v in enumerate(variables)}
    return [(sum(1 << positions[v] for v in eq.variables), eq.rhs)
            for eq in equations]


def shortest_inconsistent_subset(equations: list[XorEquation], *,
                                 max_rows: int = 40, max_variables: int = 16,
                                 max_states: int = 100000):
    """Exact shortest inconsistent equation subset under explicit caps.

    Retain a single least-cardinality, lexicographically first row-index tuple
    per syndrome state. That state dominates alternatives for all later rows.
    """
    if len(equations) > max_rows or max_rows < 0:
        raise ValueError("GF2 syndrome row cap exceeded")
    if max_states < 1:
        raise ValueError("GF2 syndrome state cap must be positive")
    masks = _masks(equations, max_variables=max_variables)
    best = {(0, 0): ()}
    peak = 1
    for index, (mask, rhs) in enumerate(masks):
        updated = dict(best)
        for (old_mask, old_rhs), selected in best.items():
            key = (old_mask ^ mask, old_rhs ^ rhs)
            proposal = selected + (index,)
            current = updated.get(key)
            if current is None or (len(proposal), proposal) < (len(current), current):
                updated[key] = proposal
        if len(updated) > max_states:
            raise ValueError("GF2 syndrome state cap exceeded")
        best = updated
        peak = max(peak, len(best))
    return best.get((0, 1)), {"peak_states": peak, "reachable_states": len(best),
                              "equations": len(equations),
                              "distinct_variables": len({v for eq in equations for v in eq.variables})}


def exhaustive_inconsistent_subset(equations: list[XorEquation], *, max_rows: int = 16):
    """Independent combinations oracle for shortest odd GF(2) dependency."""
    if len(equations) > max_rows:
        raise ValueError("exhaustive GF2 row cap exceeded")
    for count in range(1, len(equations) + 1):
        for subset in combinations(range(len(equations)), count):
            parity = 0
            variables = set()
            for index in subset:
                equation = equations[index]
                parity ^= equation.rhs
                variables.symmetric_difference_update(equation.variables)
            if not variables and parity == 1:
                return subset
    return None


def validate_witness_against_original(formula: CNFFormula,
                                      equations: list[XorEquation], indices) -> dict:
    """Fail closed unless a dependency and every source encoding are exact.

    This is an additional independent semantic audit, never a replacement
    for RUP and real external DRAT verification of a clausal proof.
    """
    if indices is None or not indices or tuple(indices) != tuple(sorted(set(indices))):
        raise ValueError("invalid or duplicate witness row indices")
    support = set()
    parity = 0
    original = {clause.literals for clause in formula.clauses}
    source_union = set()
    for index in indices:
        if type(index) is not int or not 0 <= index < len(equations):
            raise ValueError("witness row index outside source equations")
        equation = equations[index]
        expected = canonical_xor_cnf_clauses(equation.variables, equation.rhs)
        encoded = {tuple(clause) for clause in equation.source_clauses}
        if encoded != expected:
            raise ValueError("witness row source encoding incomplete or altered")
        if not expected <= original:
            raise ValueError("witness row source missing from original CNF")
        support.symmetric_difference_update(equation.variables)
        parity ^= equation.rhs
        source_union.update(expected)
    if support or parity != 1:
        raise ValueError("witness rows do not form an odd GF2 dependency")
    return {"witness_rows": len(indices), "source_clauses": len(source_union),
            "odd_dependency_verified": True, "exact_original_source_verified": True}


def parity_hypergraph(seed: int, *, n: int = 6, rows: int = 6,
                      contradictory: bool = True):
    """Plant consistent mixed-width rows, then add one inconsistent closure."""
    if not 3 <= n <= 10 or not 2 <= rows <= 12:
        raise ValueError("hypergraph generator outside bounded domain")
    rng = random.Random(seed)
    variables = list(range(1, n + 1))
    planted = {v: rng.randrange(2) for v in variables}
    original = []
    for _ in range(rows):
        size = rng.randrange(1, min(4, n) + 1)
        support = sorted(rng.sample(variables, size))
        rhs = sum(planted[v] for v in support) & 1
        original.append((support, rhs))
    chosen = rng.sample(range(rows), 3)
    result_support = set()
    result_rhs = 0
    for index in chosen:
        support, rhs = original[index]
        result_support.symmetric_difference_update(support)
        result_rhs ^= rhs
    if not result_support:
        # A null-support contradiction is valid but would be trivial. Select a
        # deterministic independent row to keep this family nontrivial.
        chosen = [0, 1]
        result_support = set(original[0][0]) ^ set(original[1][0])
        result_rhs = original[0][1] ^ original[1][1]
    if not result_support:
        raise ValueError("degenerate hypergraph seed; select another seed")
    if len(result_support) > 7:
        raise ValueError("hypergraph closure width cap exceeded")
    original.append((sorted(result_support), result_rhs ^ int(contradictory)))
    equations = [XorEquation(support, rhs,
                 source_clauses=canonical_xor_cnf_clauses(support, rhs))
                 for support, rhs in original]
    formula = CNFFormula(clause for eq in equations for clause in eq.source_clauses)
    return formula, equations


def evaluate_hypergraph(seed: int, *, n: int = 6, rows: int = 6,
                        contradictory: bool = True, compare_rust: bool = False,
                        external_checker: str | None = None):
    formula, equations = parity_hypergraph(seed, n=n, rows=rows,
                                            contradictory=contradictory)
    witness, complexity = shortest_inconsistent_subset(equations)
    independent = exhaustive_inconsistent_subset(equations)
    if witness != independent:
        raise AssertionError("syndrome DP disagrees with exhaustive GF2 oracle")
    if n <= 10 and exhaustive_sat(formula) == contradictory:
        raise AssertionError("original CNF SAT oracle disagrees with planted family")
    if contradictory:
        if witness is None:
            raise AssertionError("contradictory hypergraph missing inconsistent subset")
        validate_witness_against_original(formula, equations, witness)
        selected = [equations[i] for i in witness]
        trace = _sparse_xor_elimination_schedule(selected)["row_operation_trace"]
        opts = dict(max_proof_clauses=10000, max_proof_bytes=200000,
                    timeout_seconds=15)
        proof, error, stats = _row_trace_refutation(formula, selected, trace,
                                                   backend="python", **opts)
        if compare_rust:
            native = _row_trace_refutation(formula, selected, trace,
                                           backend="rust", **opts)
            if native != (proof, error, stats):
                raise AssertionError("native/Python hypergraph witness proof differs")
        if error is not None or not proof or not check_drat_text(formula, proof)["verified"]:
            raise AssertionError(f"hypergraph witness proof rejected: {error}")
        if external_checker is not None and not _external_check(formula, proof, external_checker):
            raise AssertionError("external checker rejected hypergraph proof")
    else:
        if witness is not None:
            raise AssertionError("consistent hypergraph must have no inconsistent witness")
        proof, stats = None, {"proof_clause_count_actual": 0}
    return {"seed": seed, "n": n, "row_count": len(equations),
            "contradictory": contradictory, "witness_rows": list(witness) if witness else None,
            "source_clauses": formula.num_clauses,
            "proof_clauses": stats["proof_clause_count_actual"],
            "original_cnf_sha256": sha256(formula.canonical_dimacs().encode()).hexdigest(),
            "proof_sha256": sha256(proof.encode()).hexdigest() if proof else None,
            "external_drat_verified": bool(proof and external_checker is not None),
            "native_differential": compare_rust, **complexity}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=32)
    parser.add_argument("--compare-rust", action="store_true")
    parser.add_argument("--drat-trim")
    args = parser.parse_args()
    if not 1 <= args.seeds <= 200:
        raise ValueError("seed count outside bounded range")
    checker = find_drat_trim(args.drat_trim) if args.drat_trim else None
    if args.drat_trim and checker is None:
        raise ValueError("requested external checker unavailable")
    records = []
    for seed in range(301000, 301000 + args.seeds):
        for contradictory in (False, True):
            try:
                records.append(evaluate_hypergraph(seed, contradictory=contradictory,
                    compare_rust=args.compare_rust, external_checker=checker))
            except ValueError as exc:
                if "degenerate hypergraph seed" not in str(exc) and "closure width cap" not in str(exc):
                    raise
    print(json.dumps({"status": "BOUNDED_HYPERGRAPH_SYNDROME_NOT_GENERAL_SAT_CLAIM",
        "cases": len(records), "unsat": sum(r["contradictory"] for r in records),
        "external_drat_verification_performed": checker is not None,
        "native_differential_performed": args.compare_rust}, sort_keys=True))


if __name__ == "__main__":
    main()
