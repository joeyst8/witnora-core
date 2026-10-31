"""Source-clause-bound Lean G14 verification of zero-separator contradiction."""
from witnora_core.cnf import CNFFormula
from witnora_core.separator_affine_family_theorem import (
    SeparatorAffineFamilyInstance,
    UNSAT_CERTIFIED,
    build_separator_affine_certificate,
)
from witnora_core.lean_g14_gate import verify_g14_unsat_cover_with_lean


def main():
    clauses = [[1], [-1]]
    formula = CNFFormula.from_raw_clauses(clauses)
    instance = SeparatorAffineFamilyInstance(
        instance_id="tc063_zero_separator_g14_lean",
        formula=formula, separator_variables=[],
        separator_bound_c=0, affine_arity_bound_r=2,
        expected_result=UNSAT_CERTIFIED, family="zero_separator", n=1)
    cert = build_separator_affine_certificate(instance)
    assert cert.final_result == UNSAT_CERTIFIED, cert.final_result
    result = verify_g14_unsat_cover_with_lean(
        formula, cert, raw_clauses=clauses,
        timeout_seconds=180)
    print(result)
    assert result.get("verified") is True, result
    assert result.get("lean_formal_status") == "LEAN_G5_COVER_AND_PARTITIONS_VERIFIED", result
    assert result.get("source_normalization_verified") is True, result


if __name__ == "__main__":
    main()
