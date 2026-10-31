"""Minimal, independently Lean-certified affine completeness stress case."""
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.operator_genesis import (
    AffineResidueInstance,
    AFFINE_RESIDUE_UNSAT_NATIVE_CERTIFIED,
    build_affine_residue_certificate,
    extract_affine_residue_equations,
    gaussian_eliminate_gf2,
)


class TC063UnitCounterexample(unittest.TestCase):
    def test_historical_width_two_cutoff_misses_unit_xors(self):
        formula = CNFFormula.from_raw_clauses([[1], [-1]])
        equations, diagnostics = extract_affine_residue_equations(
            formula, max_arity=2, min_arity=2)
        self.assertEqual(equations, [])
        # Explicit historical cutoff still skips units; production now
        # uses the complete supported [0,r] width range by default.
        cert = build_affine_residue_certificate(
            AffineResidueInstance(
                instance_id="tc063_unit_counterexample",
                equations=(), formula=formula,
            ), max_arity=2)
        self.assertEqual(cert.status, AFFINE_RESIDUE_UNSAT_NATIVE_CERTIFIED)
        self.assertEqual(cert.checker_status, "AFFINE_RESIDUE_CERTIFICATE_VERIFIED")

    def test_default_includes_both_unit_rows(self):
        formula = CNFFormula.from_raw_clauses([[1], [-1]])
        equations, _ = extract_affine_residue_equations(formula, max_arity=2)
        self.assertEqual(len(equations), 2)

    def test_empty_clause_contradiction_is_native_verified(self):
        formula = CNFFormula.from_raw_clauses([[]])
        cert = build_affine_residue_certificate(
            AffineResidueInstance(
                instance_id="tc063_empty_clause",
                equations=(), formula=formula,
            ), max_arity=2)
        self.assertEqual(cert.status, AFFINE_RESIDUE_UNSAT_NATIVE_CERTIFIED)
        self.assertEqual(cert.checker_status, "AFFINE_RESIDUE_CERTIFICATE_VERIFIED")
        self.assertEqual(cert.contradiction_row["coefficients"], [])
        self.assertEqual(cert.contradiction_row["rhs"], 1)

    def test_lower_min_arity_finds_valid_contradiction(self):
        formula = CNFFormula.from_raw_clauses([[1], [-1]])
        equations, diagnostics = extract_affine_residue_equations(
            formula, max_arity=2, min_arity=1)
        self.assertEqual(len(equations), 2, diagnostics)
        result = gaussian_eliminate_gf2(equations)
        self.assertEqual(result["status"], "UNSAT")
        self.assertIsNotNone(result["contradiction_row"])
        self.assertEqual(result["contradiction_row"]["coefficients"], [])
        self.assertEqual(result["contradiction_row"]["rhs"], 1)


if __name__ == "__main__":
    unittest.main()
