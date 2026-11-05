"""Fail-closed hostile original-CNF and certificate-boundary research matrix."""

from __future__ import annotations

import argparse
import json

from scripts.benchmark_xor_frontier import _external_check, exhaustive_sat
from scripts.benchmark_xor_heldout_401_460 import background_instance
from scripts.benchmark_xor_syndrome_frontier import (
    shortest_inconsistent_subset, validate_witness_against_original,
)
from witnora_core.cnf import CNFFormula
from witnora_core.drat_check import check_drat_text
from witnora_core.drat_trim import find_drat_trim
from witnora_core.xor import XorEquation
from witnora_core.xor_drat import _row_trace_refutation, _sparse_xor_elimination_schedule


def hostile_fixture(seed):
    formula, rows, _ = background_instance(seed, contradictory=True)
    witness, state = shortest_inconsistent_subset(rows)
    selected = [rows[i] for i in witness]
    trace = _sparse_xor_elimination_schedule(selected)["row_operation_trace"]
    return formula, rows, witness, selected, trace, state


def attempt_proof(formula, selected, trace, *, backend="python", **limits):
    return _row_trace_refutation(formula, selected, trace, backend=backend,
        **{**dict(max_proof_clauses=10000, max_proof_bytes=200000,
                 timeout_seconds=15), **limits})


def hostile_report(seed, *, external_checker=None, compare_rust=False):
    formula, rows, witness, selected, trace, states = hostile_fixture(seed)
    validate_witness_against_original(formula, rows, witness)
    proof, error, stats = attempt_proof(formula, selected, trace)
    if error is not None or not check_drat_text(formula, proof)["verified"]:
        raise AssertionError("reference proof rejected")
    if external_checker and not _external_check(formula, proof, external_checker):
        raise AssertionError("external original-CNF checker rejected proof")
    if compare_rust and attempt_proof(formula, selected, trace, backend="rust") != (
            proof, error, stats):
        raise AssertionError("Rust and Python diverge on hostile original CNF")
    target = tuple(selected[0].source_clauses[0])
    missing = CNFFormula(c for c in formula.to_clause_lists() if tuple(c) != target)
    try:
        validate_witness_against_original(missing, rows, witness)
    except ValueError:
        pass
    else:
        raise AssertionError("missing original source was silently accepted")
    missing_proof, missing_error, _ = attempt_proof(missing, selected, trace)
    if missing_proof is not None or missing_error != "DETECTED_XOR_SOURCE_CLAUSE_MISSING_FROM_ORIGINAL":
        raise AssertionError("missing source did not fail closed before proof")
    old = rows[witness[0]]
    forged = list(rows)
    forged[witness[0]] = XorEquation(old.variables, old.rhs ^ 1,
                                     source_clauses=old.source_clauses)
    try:
        validate_witness_against_original(formula, forged, witness)
    except ValueError:
        pass
    else:
        raise AssertionError("forged row metadata passed audit")
    clauses = stats["proof_clause_count_actual"]
    bytes_count = stats["proof_file_size_bytes"]
    if attempt_proof(formula, selected, trace, max_proof_clauses=clauses) != (
            proof, error, stats):
        raise AssertionError("exact proof clause budget changed output")
    if attempt_proof(formula, selected, trace, max_proof_bytes=bytes_count) != (
            proof, error, stats):
        raise AssertionError("exact proof byte budget changed output")
    if attempt_proof(formula, selected, trace, max_proof_clauses=clauses-1)[1] != "SKIPPED_PROOF_SIZE_CAP":
        raise AssertionError("under-budget clause candidate not rejected")
    if attempt_proof(formula, selected, trace, max_proof_bytes=bytes_count-1)[1] != "SKIPPED_PROOF_BYTES_CAP":
        raise AssertionError("under-budget byte candidate not rejected")
    sat_formula, sat_rows, _ = background_instance(seed, contradictory=False)
    if not exhaustive_sat(sat_formula) or shortest_inconsistent_subset(sat_rows)[0] is not None:
        raise AssertionError("SAT control improperly certified")
    return {"seed": seed, "verified_original": True,
            "external_original_verified": bool(external_checker),
            "native_differential": compare_rust,
            "missing_source_rejected": True, "forged_metadata_rejected": True,
            "exact_proof_budget_accepted": True, "one_below_budget_rejected": True,
            "sat_control_preserved": True, "proof_clauses": clauses,
            "proof_bytes": bytes_count, **states}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=32)
    parser.add_argument("--compare-rust", action="store_true")
    parser.add_argument("--drat-trim")
    args = parser.parse_args()
    if not 1 <= args.samples <= 80:
        raise ValueError("hostile sample cap exceeded")
    checker = find_drat_trim(args.drat_trim) if args.drat_trim else None
    if args.drat_trim and not checker:
        raise ValueError("requested external checker missing")
    reports = [hostile_report(seed, external_checker=checker,
                              compare_rust=args.compare_rust)
               for seed in range(461000, 461000 + args.samples)]
    print(json.dumps({"status": "HOSTILE_PROOF_BOUNDARIES_FINITE_RESEARCH_ONLY",
        "cases": len(reports), "external_verified": bool(checker),
        "native_differential": args.compare_rust,
        "all_hostile_rejections": all(r["missing_source_rejected"] and
            r["forged_metadata_rejected"] and r["one_below_budget_rejected"]
            for r in reports)}, sort_keys=True))


if __name__ == "__main__":
    main()
