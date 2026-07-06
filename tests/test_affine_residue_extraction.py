import unittest

from witnora_core.operator_genesis import (
    AFFINE_RESIDUE_EXTRACTION_INCOMPLETE_REJECTED,
    AFFINE_RESIDUE_OVER_CAP_DIAGNOSTIC,
    extract_affine_residue_equations,
    make_affine_residue_instance,
)


class AffineResidueExtractionTest(unittest.TestCase):
    def test_affine_full_encoding_extraction(self):
        instance = make_affine_residue_instance("parity_arity_8_unsat")
        equations, diagnostics = extract_affine_residue_equations(instance.formula, max_arity=10)
        self.assertEqual(len(equations), 2)
        self.assertEqual({eq["parity_bit"] for eq in equations}, {0, 1})
        self.assertEqual({eq["arity"] for eq in equations}, {8})
        print("AFFINE_FULL_ENCODING_EXTRACTION_PASS")

    def test_affine_incomplete_encoding_reject(self):
        instance = make_affine_residue_instance("incomplete_affine_reject")
        equations, diagnostics = extract_affine_residue_equations(instance.formula, max_arity=10)
        self.assertFalse(equations)
        self.assertTrue(any(item["status"] == AFFINE_RESIDUE_EXTRACTION_INCOMPLETE_REJECTED for item in diagnostics))
        print("AFFINE_INCOMPLETE_ENCODING_REJECT_PASS")

    def test_affine_polluted_encoding_no_false_claim(self):
        instance = make_affine_residue_instance("polluted_affine_reject")
        equations, diagnostics = extract_affine_residue_equations(instance.formula, max_arity=10)
        self.assertFalse(equations)
        self.assertTrue(diagnostics)
        print("AFFINE_POLLUTED_ENCODING_NO_FALSE_CLAIM_PASS")

    def test_affine_over_cap_diagnostic(self):
        instance = make_affine_residue_instance("over_cap_affine_diagnostic")
        equations, diagnostics = extract_affine_residue_equations(instance.formula, max_arity=10)
        self.assertFalse(equations)
        self.assertTrue(any(item["status"] == AFFINE_RESIDUE_OVER_CAP_DIAGNOSTIC for item in diagnostics))
        print("AFFINE_OVER_CAP_DIAGNOSTIC_PASS")


if __name__ == "__main__":
    unittest.main()
