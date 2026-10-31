"""Fail-closed Lean acceptance of actual native G5 unit/empty certificates."""
from witnora_core.cnf import CNFFormula
from witnora_core.operator_genesis import (
    AFFINE_RESIDUE_CERTIFICATE_VERIFIED,
    AFFINE_RESIDUE_UNSAT_NATIVE_CERTIFIED,
    AffineResidueInstance,
    build_affine_residue_certificate,
)
from witnora_core.lean_g5_gate import verify_g5_certificate_with_lean


def main():
    for label, clauses in (
        ("unit_contradiction", [[1], [-1]]),
        ("empty_clause", [[]]),
    ):
        formula = CNFFormula.from_raw_clauses(clauses)
        cert = build_affine_residue_certificate(
            AffineResidueInstance(instance_id=label, equations=(),
                                  formula=formula),
            max_arity=2,
        )
        assert cert.status == AFFINE_RESIDUE_UNSAT_NATIVE_CERTIFIED, (label, cert.status)
        assert cert.checker_status == AFFINE_RESIDUE_CERTIFICATE_VERIFIED, (label, cert.checker_status)
        result = verify_g5_certificate_with_lean(
            formula, cert, max_arity=2,
            raw_clauses=clauses,
            timeout_seconds=180,
        )
        print(label, result)
        assert result.get("verified") is True, (label, result)
        assert result.get("lean_formal_status") == "LEAN_VERIFIED", (label, result)
        assert result.get("source_normalization_verified") is True, (label, result)


if __name__ == "__main__":
    main()
