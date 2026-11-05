"""Research-only linear chain XOR contradiction with original-CNF proof checks."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json

from scripts.benchmark_xor_frontier import _external_check, exhaustive_sat
from witnora_core.cnf import CNFFormula
from witnora_core.drat_check import check_drat_text
from witnora_core.drat_trim import find_drat_trim
from witnora_core.xor import XorEquation, canonical_xor_cnf_clauses
from witnora_core.xor_drat import _row_trace_refutation, _sparse_xor_elimination_schedule


def chain(n: int, *, contradictory: bool = True,
          variable_gap: int = 1, reverse_clauses: bool = False):
    if not 2 <= n <= 80 or not 1 <= variable_gap <= 1000:
        raise ValueError("chain size or label gap outside bounded domain")
    ids = [variable_gap * i for i in range(1, n + 1)]
    rows = [([ids[i], ids[i + 1]], 0) for i in range(n - 1)]
    rows.extend([([ids[0]], 0), ([ids[-1]], int(contradictory))])
    equations = [XorEquation(variables, rhs,
        source_clauses=canonical_xor_cnf_clauses(variables, rhs))
        for variables, rhs in rows]
    clauses = [clause for equation in equations for clause in equation.source_clauses]
    if reverse_clauses:
        clauses.reverse()
    formula = CNFFormula(clauses)
    trace = _sparse_xor_elimination_schedule(equations)["row_operation_trace"]
    return formula, equations, trace


def measure_chain(n: int, *, contradictory: bool = True, compare_rust: bool = False,
                  external_checker: str | None = None, variable_gap: int = 1,
                  reverse_clauses: bool = False, max_proof_clauses: int = 500,
                  max_proof_bytes: int = 10000):
    formula, equations, trace = chain(n, contradictory=contradictory,
        variable_gap=variable_gap, reverse_clauses=reverse_clauses)
    opts = dict(max_proof_clauses=max_proof_clauses,
                max_proof_bytes=max_proof_bytes, timeout_seconds=15)
    proof, error, stats = _row_trace_refutation(formula, equations, trace,
                                               backend="python", **opts)
    if compare_rust:
        actual = _row_trace_refutation(formula, equations, trace,
                                       backend="rust", **opts)
        if actual != (proof, error, stats):
            raise AssertionError(f"native/Python disagreement for chain n={n}")
    if contradictory and error is None:
        if not proof or not check_drat_text(formula, proof)["verified"]:
            raise AssertionError("chain candidate not original-CNF RUP accepted")
        if external_checker is not None and not _external_check(formula, proof, external_checker):
            raise AssertionError("external drat-trim rejected chain proof")
    elif not contradictory and (proof is not None or error != "ROW_OPERATION_TRACE_DID_NOT_DERIVE_EMPTY"):
        raise AssertionError("satisfiable chain incorrectly emitted an UNSAT candidate")
    return {"n": n, "contradictory": contradictory,
            "source_clauses": formula.num_clauses,
            "trace_operations": len(trace),
            "proof_clauses": stats["proof_clause_count_actual"],
            "proof_bytes": stats["proof_file_size_bytes"],
            "status": "CANDIDATE_RUP_ACCEPTED" if proof else error,
            "original_cnf_sha256": sha256(formula.canonical_dimacs().encode()).hexdigest(),
            "proof_sha256": sha256(proof.encode()).hexdigest() if proof else None,
            "external_drat_verified": bool(proof and external_checker is not None),
            "native_differential": compare_rust}


def run_chains(*, compare_rust: bool = False, external_checker: str | None = None):
    if external_checker is not None:
        external_checker = find_drat_trim(external_checker)
        if external_checker is None:
            raise ValueError("external checker explicitly requested but unavailable")
    sizes = (2, 3, 4, 5, 8, 10, 16, 20, 40, 80)
    rows = [measure_chain(n, compare_rust=compare_rust,
                          external_checker=external_checker) for n in sizes]
    return {"status": "BOUNDED_CHAIN_SCALING_NOT_GENERAL_SAT_CLAIM",
            "external_drat_verification_performed": external_checker is not None,
            "native_differential_performed": compare_rust, "rows": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compare-rust", action="store_true")
    parser.add_argument("--drat-trim")
    args = parser.parse_args()
    print(json.dumps(run_chains(compare_rust=args.compare_rust,
        external_checker=args.drat_trim), sort_keys=True))


if __name__ == "__main__":
    main()
