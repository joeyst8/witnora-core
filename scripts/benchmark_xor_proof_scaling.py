"""Measure proof growth on a controlled, full-encoding XOR contradiction.

One pair of opposing k-variable XORs is intentionally easy to recognize but
forces exponentially many source clauses in the complete CNF representation.
The measured proof sizes describe this exporter/family only, not a SAT bound.
"""

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


def contradiction(width: int):
    if not 1 <= width <= 12:
        raise ValueError("scaling width must lie in [1,12]")
    variables = list(range(1, width + 1))
    equations = [XorEquation(variables, rhs,
        source_clauses=canonical_xor_cnf_clauses(variables, rhs)) for rhs in (0, 1)]
    formula = CNFFormula(c for equation in equations for c in equation.source_clauses)
    trace = _sparse_xor_elimination_schedule(equations)["row_operation_trace"]
    return formula, equations, trace


def measure(width: int, *, compare_rust: bool = False,
            external_checker: str | None = None,
            max_proof_clauses: int = 5000,
            max_proof_bytes: int = 200000):
    formula, equations, trace = contradiction(width)
    opts = dict(max_proof_clauses=max_proof_clauses,
                max_proof_bytes=max_proof_bytes, timeout_seconds=15)
    proof, error, stats = _row_trace_refutation(formula, equations, trace,
                                               backend="python", **opts)
    if compare_rust:
        rust_proof, rust_error, rust_stats = _row_trace_refutation(
            formula, equations, trace, backend="rust", **opts)
        if (rust_proof, rust_error, rust_stats) != (proof, error, stats):
            raise AssertionError(f"width {width} Python/Rust disagreement")
    if error is not None or proof is None:
        return {"width": width, "status": error, "source_clauses": formula.num_clauses,
                "proof_clauses": stats["proof_clause_count_actual"],
                "proof_bytes": stats["proof_file_size_bytes"],
                "original_cnf_sha256": sha256(formula.canonical_dimacs().encode()).hexdigest()}
    if not check_drat_text(formula, proof)["verified"]:
        raise AssertionError(f"width {width} original-CNF RUP check failed")
    if external_checker is not None and not _external_check(formula, proof, external_checker):
        raise AssertionError(f"width {width} independent DRAT checker rejected proof")
    return {"width": width, "status": "CANDIDATE_RUP_ACCEPTED",
            "source_clauses": formula.num_clauses,
            "proof_clauses": stats["proof_clause_count_actual"],
            "proof_bytes": stats["proof_file_size_bytes"],
            "peak_proof_width": stats["proof_clause_max_width"],
            "original_cnf_sha256": sha256(formula.canonical_dimacs().encode()).hexdigest(),
            "proof_sha256": sha256(proof.encode()).hexdigest(),
            "external_drat_verified": external_checker is not None,
            "rust_differential_verified": compare_rust}


def run_scaling(max_width: int = 10, *, compare_rust: bool = False,
                external_checker: str | None = None):
    if not 1 <= max_width <= 12:
        raise ValueError("max width outside bounded domain")
    if external_checker is not None:
        external_checker = find_drat_trim(external_checker)
        if external_checker is None:
            raise ValueError("external checker requested but unavailable")
    rows = [measure(w, compare_rust=compare_rust, external_checker=external_checker)
            for w in range(1, max_width + 1)]
    return {"status": "BOUNDED_EXPORTER_SCALING_NOT_COMPLEXITY_THEOREM",
            "max_width": max_width,
            "external_drat_verification_performed": external_checker is not None,
            "native_differential_performed": compare_rust,
            "rows": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-width", type=int, default=10)
    parser.add_argument("--compare-rust", action="store_true")
    parser.add_argument("--drat-trim", type=str)
    args = parser.parse_args()
    result = run_scaling(args.max_width, compare_rust=args.compare_rust,
                         external_checker=args.drat_trim)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
