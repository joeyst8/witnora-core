"""Exhaustive small TC-063 G14 adversary: independent Boolean truth tables.

64 generated combinations before removal of the variable-free/no-clause case.
Each combines one supported two-variable XOR residual across the two
separator branches with zero, one or both separator-only unit clauses.
No SAT/UNSAT label is inferred from Witnora's own certificate.
"""
from __future__ import annotations

from itertools import product
import json

from witnora_core.cnf import CNFFormula
from witnora_core.xor import canonical_xor_cnf_clauses
from witnora_core.separator_affine_family_theorem import (
    SeparatorAffineFamilyInstance,
    SAT_CERTIFIED,
    UNSAT_CERTIFIED,
    build_separator_affine_certificate,
    check_separator_affine_certificate,
)
from witnora_core.cnf import formula_satisfied


PARITY_SETS = ((), (0,), (1,), (0, 1))
SEPARATOR_UNITS = ((), (1,), (-1,), (1, -1))


def independent_oracle(formula: CNFFormula) -> bool:
    variables = sorted(formula.variables)
    return any(
        formula_satisfied(formula, dict(zip(variables, values)))
        for values in product((False, True), repeat=len(variables))
    )


def family_formula(false_rows, true_rows, separator_units):
    clauses = []
    for rhs in false_rows:
        for clause in canonical_xor_cnf_clauses((2, 3), rhs):
            clauses.append(sorted([1, *clause]))
    for rhs in true_rows:
        for clause in canonical_xor_cnf_clauses((2, 3), rhs):
            clauses.append(sorted([-1, *clause]))
    clauses.extend([[literal] for literal in separator_units])
    return CNFFormula.from_raw_clauses(clauses)


def run_exhaustive():
    tested = 0
    unique = set()
    verdicts = {SAT_CERTIFIED: 0, UNSAT_CERTIFIED: 0}
    failures = []
    first = None
    for false_rows, true_rows, units in product(
            PARITY_SETS, PARITY_SETS, SEPARATOR_UNITS):
        formula = family_formula(false_rows, true_rows, units)
        if 1 not in formula.variables:
            continue
        if formula.formula_hash in unique:
            continue
        unique.add(formula.formula_hash)
        tested += 1
        expected = SAT_CERTIFIED if independent_oracle(formula) else UNSAT_CERTIFIED
        item = SeparatorAffineFamilyInstance(
            instance_id=f"tc063_exhaustive_{tested}",
            formula=formula,
            separator_variables=[1], separator_bound_c=1,
            affine_arity_bound_r=2, expected_result=expected,
            family="tc063_exhaustive", n=1,
        )
        cert = build_separator_affine_certificate(item)
        checked = check_separator_affine_certificate(formula, cert)
        actual = cert.final_result
        if actual in verdicts:
            verdicts[actual] += 1
        record = {
            "index": tested,
            "false_rows": list(false_rows),
            "true_rows": list(true_rows),
            "separator_units": list(units),
            "clauses": formula.to_clause_lists(),
            "formula_hash": formula.formula_hash,
            "oracle": expected,
            "producer": actual,
            "native_checker": checked["status"],
            "checker_errors": checked["errors"],
        }
        if first is None:
            first = record
        if actual != expected or checked["status"] != "SEPARATOR_AFFINE_CERTIFICATE_VERIFIED":
            failures.append(record)

    summary = {
        "generated_parameter_combinations": 64,
        "unique_tested": tested,
        "verified_results": verdicts,
        "failures": len(failures),
        "first_failure": failures[0] if failures else None,
    }
    print(json.dumps(summary, sort_keys=True))
    assert tested >= 40, summary
    assert not failures, summary
    assert all(value > 0 for value in verdicts.values()), summary
    return summary


if __name__ == "__main__":
    run_exhaustive()
