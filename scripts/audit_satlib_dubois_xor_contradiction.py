"""Independent source-clause checker for Dubois20's XOR contradiction.

The extractor may suggest equations, but the certificate *verifier* accepts
only original signed clauses and an explicit row list. It checks every
Boolean assignment over each row's stated variables and independently
confirms the XOR of the checked rows is 0 = 1. No SAT-solver UNSAT answer is
used in this source-level certificate. This is not a Lean kernel proof.
"""
from __future__ import annotations

import argparse
import json
from itertools import product

from scripts.experiment_satlib_nonparity_diversity_gate import fetch_frozen_source
from witnora_core.cnf import CNFFormula
from witnora_core.xor import detect_cnf_xor_patterns


def verify_xor_refutation(raw_clauses, nvars, proof_equations, *, max_width=8):
    """Check source implication row by row, then the final GF(2) identity."""
    source = {frozenset(c.literals) for c in CNFFormula(raw_clauses).clauses}
    if not proof_equations or len(proof_equations) > 4096:
        raise ValueError("empty or oversized XOR proof")
    union_clauses = set()
    all_mask = 0
    all_rhs = 0
    for index, proof in enumerate(proof_equations):
        variables = tuple(proof["variables"])
        rhs = proof["rhs"]
        if not (1 <= len(variables) <= max_width and rhs in (0, 1)
                and len(set(variables)) == len(variables)
                and all(isinstance(v, int) and 1 <= v <= nvars for v in variables)):
            raise ValueError(f"invalid exact XOR row {index}")
        clauses = [tuple(c) for c in proof["source_clauses"]]
        if not clauses or any(frozenset(c) not in source for c in clauses):
            raise ValueError("proof references absent original source clauses")
        if any(any(abs(l) not in variables for l in c) for c in clauses):
            raise ValueError("row source clause uses an unlisted variable")
        for truth in product((False, True), repeat=len(variables)):
            assignment = dict(zip(variables, truth))
            group_truth = all(any(assignment[abs(lit)] == (lit > 0) for lit in c)
                              for c in clauses)
            parity_truth = (sum(truth) & 1) == rhs
            if group_truth != parity_truth:
                raise AssertionError("source clause group is not exactly stated XOR")
        union_clauses.update(frozenset(c) for c in clauses)
        for v in variables:
            all_mask ^= 1 << (v - 1)
        all_rhs ^= rhs
    if all_mask != 0 or all_rhs != 1:
        raise AssertionError("XOR of checked rows is not the contradiction 0 = 1")
    return {"status": "CHECKED_SOURCE_XOR_CONTRADICTION",
            "proof_rows": len(proof_equations),
            "distinct_source_clauses_covered": len(union_clauses),
            "lhs_variable_mask": 0, "rhs": 1,
            "finite_row_truth_tables_checked": True,
            "lean_kernel_checked": False}


def derive_candidate_refutation(raw_clauses, nvars):
    """Use source-exact detector only to *propose* independently checked rows."""
    detected = detect_cnf_xor_patterns(CNFFormula(raw_clauses))
    extracted = [e for e in detected.equations
                 if e.safe_use and e.exact_full_encoding]
    equations = [{"variables": list(eq.variables), "rhs": int(eq.rhs),
                  "source_clauses": [list(c) for c in eq.source_clauses]}
                 for eq in extracted]
    pivots = {}
    selected = None
    for index, eq in enumerate(equations):
        mask = 0
        for v in eq["variables"]:
            mask ^= 1 << (v - 1)
        rhs = eq["rhs"]
        provenance = {index}
        while mask:
            pivot = mask.bit_length()
            old = pivots.get(pivot)
            if old is None:
                pivots[pivot] = (mask, rhs, provenance)
                break
            previous_mask, previous_rhs, previous_provenance = old
            mask ^= previous_mask
            rhs ^= previous_rhs
            provenance ^= previous_provenance
        else:
            if rhs:
                selected = tuple(sorted(provenance))
                break
    if selected is None:
        return {"status": "UNKNOWN_NO_EXTRACTED_XOR_CONTRADICTION",
                "source_exact_xor_rows": len(equations)}
    proof = [equations[i] for i in selected]
    result = verify_xor_refutation(raw_clauses, nvars, proof)
    return {**result, "source_exact_xor_rows": len(equations),
            "proof_equation_ids": list(selected),
            "proof_equations": proof}


def audit_dubois20():
    source = fetch_frozen_source("dubois20.cnf.Z")
    result = derive_candidate_refutation(source["clause_lists"],
                                         source["variables"])
    return {"source": source["source"], "sha256": source["sha256"],
            "original_variables": source["variables"],
            "original_clauses": source["clauses"], **result}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-certificate", action="store_true")
    args = parser.parse_args()
    report = audit_dubois20()
    if not args.full_certificate:
        report.pop("proof_equations", None)
    print(json.dumps(report, indent=2))
