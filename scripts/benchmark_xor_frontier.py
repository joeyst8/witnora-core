"""Bounded, reproducible research checks for XOR proof candidates.

The exhaustive SAT oracle is deliberately independent of both XOR elimination
and the Python/Rust RUP checkers.  It is usable only on small formulas; it is
not a new SAT algorithm and never upgrades an UNSAT claim to external proof.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import random
from tempfile import TemporaryDirectory

from witnora_core.cnf import CNFFormula
from witnora_core.drat_check import check_drat_text
from witnora_core.drat_trim import find_drat_trim, run_drat_trim
from witnora_core.xor import XorEquation, canonical_xor_cnf_clauses
from witnora_core.xor_drat import _row_trace_refutation, _sparse_xor_elimination_schedule


def exhaustive_sat(formula: CNFFormula, *, variable_cap: int = 12) -> bool:
    """Independent truth-table evaluator of the *original* CNF."""
    variables = formula.variables
    if len(variables) > variable_cap:
        raise ValueError("exhaustive oracle variable cap exceeded")
    for bits in product((False, True), repeat=len(variables)):
        assignment = dict(zip(variables, bits))
        if all(any(assignment[abs(lit)] == (lit > 0) for lit in clause)
               for clause in formula.clauses):
            return True
    return False


def build_case(seed: int, *, width: int, contradictory: bool,
               overlap: bool, shuffle: bool, sparse_ids: bool) -> tuple[CNFFormula, list[XorEquation], list[dict]]:
    """Planted SAT controls paired with exact contradictory XOR UNSAT cases."""
    if width not in (1, 2, 3):
        raise ValueError("research proof width must be 1 through 3")
    rng = random.Random(seed)
    candidates = list(range(1, 10)) if not sparse_ids else [2, 13, 37, 99, 211, 613, 997]
    variables = sorted(rng.sample(candidates, width))
    auxiliary = list(range(20, 26)) if not sparse_ids else [1201, 1301, 1601, 1901]
    planted = {v: bool(rng.randrange(2)) for v in variables + auxiliary}
    rhs = sum(planted[v] for v in variables) & 1
    rights = (rhs, rhs ^ 1) if contradictory else (rhs,)
    equations = [XorEquation(variables, bit,
                 source_clauses=canonical_xor_cnf_clauses(variables, bit))
                 for bit in rights]
    clauses = [list(clause) for equation in equations for clause in equation.source_clauses]
    pool = variables + auxiliary if overlap else auxiliary
    for _ in range(4):
        support = rng.sample(pool, rng.randrange(1, min(4, len(pool)) + 1))
        clause = [v if rng.randrange(2) else -v for v in support]
        if not any(planted[abs(lit)] == (lit > 0) for lit in clause):
            clause[0] = abs(clause[0]) if planted[abs(clause[0])] else -abs(clause[0])
        clauses.append(clause)
    if shuffle:
        clauses.extend(clauses[:min(3, len(clauses))])
        rng.shuffle(clauses)
    formula = CNFFormula(clauses)
    trace = _sparse_xor_elimination_schedule(equations)["row_operation_trace"]
    return formula, equations, trace


def _external_check(formula: CNFFormula, proof: str, checker: str) -> bool:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        cnf_path = root / "original.dimacs"
        proof_path = root / "proof.drat"
        cnf_path.write_text(formula.canonical_dimacs(), encoding="utf-8")
        proof_path.write_text(proof, encoding="utf-8")
        result = run_drat_trim(cnf_path, proof_path, checker, timeout_seconds=15)
        return bool(result["external_checker_verified"])


def exercise_case(seed: int, *, width: int, contradictory: bool,
                  overlap: bool, shuffle: bool, sparse_ids: bool,
                  compare_rust: bool = False, external_checker: str | None = None) -> dict:
    formula, equations, trace = build_case(seed, width=width,
        contradictory=contradictory, overlap=overlap, shuffle=shuffle, sparse_ids=sparse_ids)
    actual_sat = exhaustive_sat(formula)
    if actual_sat == contradictory:
        raise AssertionError("exhaustive original-CNF oracle disagrees with planted family")
    options = dict(max_proof_clauses=2000, max_proof_bytes=40000, timeout_seconds=None)
    python = _row_trace_refutation(formula, equations, trace, backend="python", **options)
    if compare_rust:
        rust = _row_trace_refutation(formula, equations, trace, backend="rust", **options)
        if rust != python:
            raise AssertionError("native/Python proof candidate or error disagrees")
    proof, error, stats = python
    if contradictory:
        if proof is None or error is not None:
            raise AssertionError(f"expected proof candidate: {error}")
        if not check_drat_text(formula, proof)["verified"]:
            raise AssertionError("independent original-CNF RUP subset check failed")
        if external_checker is not None and not _external_check(formula, proof, external_checker):
            raise AssertionError("external drat-trim rejected proof candidate")
    elif proof is not None or error != "ROW_OPERATION_TRACE_DID_NOT_DERIVE_EMPTY":
        raise AssertionError(f"SAT control emitted proof or unexpected status: {error}")
    return {
        "case_sha256": sha256(formula.canonical_dimacs().encode()).hexdigest(),
        "seed": seed, "width": width, "contradictory": contradictory,
        "overlap": overlap, "shuffled_and_duplicated": shuffle, "sparse_ids": sparse_ids,
        "cnf_variables": formula.num_vars, "cnf_clauses": formula.num_clauses,
        "exhaustive_original_cnf_sat": actual_sat,
        "proof_candidate_sha256": sha256(proof.encode()).hexdigest() if proof else None,
        "proof_clauses": stats["proof_clause_count_actual"],
        "rup_subset_verified": bool(proof),
        "external_drat_verified": bool(proof and external_checker is not None),
        "backend_differential_verified": compare_rust,
        "error": error,
    }


def run_suite(*, seeds: int = 3, compare_rust: bool = False,
              external_checker: str | None = None) -> dict:
    """48 cases per seed: matched SAT/UNSAT controls in 24 structural families."""
    if not 1 <= seeds <= 100:
        raise ValueError("seeds must lie in [1, 100]")
    if external_checker is not None:
        external_checker = find_drat_trim(external_checker)
        if external_checker is None:
            raise ValueError("explicit external drat-trim executable is unavailable")
    records = []
    for width, overlap, shuffle, sparse_ids, contradictory in product(
            (1, 2, 3), (False, True), (False, True), (False, True), (False, True)):
        for index in range(seeds):
            seed = 181000 + index + 100 * width + 1000 * int(overlap) + 2000 * int(shuffle) + 4000 * int(sparse_ids)
            records.append(exercise_case(seed, width=width, contradictory=contradictory,
                overlap=overlap, shuffle=shuffle, sparse_ids=sparse_ids,
                compare_rust=compare_rust, external_checker=external_checker))
    cases_unsat = sum(record["contradictory"] for record in records)
    return {"status": "BOUNDED_RESEARCH_CHECKS_PASSED_NOT_GENERAL_SAT_CLAIM",
            "cases": len(records), "independently_enumerated_unsat": cases_unsat,
            "independently_enumerated_sat": len(records) - cases_unsat,
            "native_python_differential": compare_rust,
            "external_drat_verification_performed": external_checker is not None,
            "records": records}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--compare-rust", action="store_true")
    parser.add_argument("--drat-trim", help="explicit independent drat-trim executable")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = run_suite(seeds=args.seeds, compare_rust=args.compare_rust,
                       external_checker=args.drat_trim)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(rendered, encoding="utf-8")
    print(json.dumps({key: val for key, val in result.items() if key != "records"}, sort_keys=True))


if __name__ == "__main__":
    main()
