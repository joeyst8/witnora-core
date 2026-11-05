"""Run complete source-text Lean G14 UNSAT gate on separator-only controls."""
from witnora_core.cnf import CNFFormula
from witnora_core.dimacs import parse_dimacs_with_text_evidence
from witnora_core.lean_g14_gate import verify_g14_unsat_cover_with_lean
from witnora_core.separator_affine_family_theorem import (
    SeparatorAffineFamilyInstance, UNSAT_CERTIFIED, SAT_CERTIFIED,
    build_separator_affine_certificate,
)


def make(name, clauses):
    formula = CNFFormula.from_raw_clauses(clauses)
    return SeparatorAffineFamilyInstance(
        instance_id=name, formula=formula, separator_variables=[1],
        separator_bound_c=1, affine_arity_bound_r=2,
        expected_result="test", family="separator_only", n=1)


def verify(item):
    source = item.formula.canonical_dimacs()
    formula, raw, tokens, spellings = parse_dimacs_with_text_evidence(source)
    cert = build_separator_affine_certificate(item)
    result = verify_g14_unsat_cover_with_lean(
        formula, cert, raw_clauses=raw, source_tokens=tokens,
        source_spellings=spellings, source_text=source,
        timeout_seconds=180)
    print(item.instance_id, cert.final_result, result)
    return cert, result


def main():
    unsat, accepted = verify(make("separator_only_unsat", [[1], [-1]]))
    assert unsat.final_result == UNSAT_CERTIFIED
    assert accepted.get("verified") is True, accepted
    assert accepted.get("lean_formal_status") == "LEAN_END_TO_END_G14_UNSAT_VERIFIED", accepted
    assert accepted.get("source_document_verified") is True

    sat, rejected = verify(make("separator_only_sat", [[1]]))
    assert sat.final_result == SAT_CERTIFIED
    assert rejected.get("verified") is False, rejected
    assert rejected.get("lean_formal_status") == "NOT_LEAN_VERIFIED", rejected


if __name__ == "__main__":
    main()
