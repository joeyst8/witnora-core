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
    def test_default_extractor_misses_contradictory_unit_xors(self):
        formula = CNFFormula.from_raw_clauses([[1], [-1]])
        equations, diagnostics = extract_affine_residue_equations(
            formula, max_arity=2)
        self.assertEqual(equations, [])
        # This is a supported semantically exact unit affine system in Lean,
        # yet default Python production skips widths below two.
        cert = build_affine_residue_certificate(
            AffineResidueInstance(
                instance_id="tc063_unit_counterexample",
                equations=(), formula=formula,
            ), max_arity=2)
        self.assertNotEqual(cert.status, AFFINE_RESIDUE_UNSAT_NATIVE_CERTIFIED)

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
