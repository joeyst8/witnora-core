"""Exhaustive small TC-063 G14 adversary: independent Boolean truth tables.

1,088 generated parameter combinations with one or two residual components.
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


def family_formula(branch_rows, separator_units):
    clauses = []
    component_count = len(branch_rows) // 2
    for component in range(component_count):
        variables = (2 + 2 * component, 3 + 2 * component)
        false_rows = branch_rows[2 * component]
        true_rows = branch_rows[2 * component + 1]
        for rhs in false_rows:
            for clause in canonical_xor_cnf_clauses(variables, rhs):
                clauses.append(sorted([1, *clause]))
        for rhs in true_rows:
            for clause in canonical_xor_cnf_clauses(variables, rhs):
                clauses.append(sorted([-1, *clause]))
    clauses.extend([[literal] for literal in separator_units])
    return CNFFormula.from_raw_clauses(clauses)


def run_exhaustive():
    tested = 0
    unique = set()
    verdicts = {SAT_CERTIFIED: 0, UNSAT_CERTIFIED: 0}
    failures = []
    by_component_count = {}
    for component_count in (1, 2):
        group_tested = 0
        for choices in product(PARITY_SETS, repeat=2 * component_count):
            for units in SEPARATOR_UNITS:
                formula = family_formula(choices, units)
                if 1 not in formula.variables:
                    continue
                if formula.formula_hash in unique:
                    continue
                unique.add(formula.formula_hash)
                tested += 1
                group_tested += 1
                expected = SAT_CERTIFIED if independent_oracle(formula) else UNSAT_CERTIFIED
                item = SeparatorAffineFamilyInstance(
                    instance_id=f"tc063_exhaustive_{tested}",
                    formula=formula,
                    separator_variables=[1], separator_bound_c=1,
                    affine_arity_bound_r=2, expected_result=expected,
                    family="tc063_exhaustive", n=component_count,
                )
                cert = build_separator_affine_certificate(item)
                checked = check_separator_affine_certificate(formula, cert)
                actual = cert.final_result
                if actual in verdicts:
                    verdicts[actual] += 1
                record = {
                    "index": tested,
                    "component_count": component_count,
                    "branch_rows": [list(x) for x in choices],
                    "separator_units": list(units),
                    "clauses": formula.to_clause_lists(),
                    "formula_hash": formula.formula_hash,
                    "oracle": expected,
                    "producer": actual,
                    "native_checker": checked["status"],
                    "checker_errors": checked["errors"],
                }
                if actual != expected or checked["status"] != "SEPARATOR_AFFINE_CERTIFICATE_VERIFIED":
                    failures.append(record)
        by_component_count[component_count] = group_tested

    summary = {
        "generated_parameter_combinations": 64 + 1024,
        "unique_tested": tested,
        "by_component_count": by_component_count,
        "verified_results": verdicts,
        "failures": len(failures),
        "first_failure": failures[0] if failures else None,
    }
    print(json.dumps(summary, sort_keys=True))
    assert tested >= 1000, summary
    assert not failures, summary
    assert all(value > 0 for value in verdicts.values()), summary
    return summary


if __name__ == "__main__":
    run_exhaustive()
