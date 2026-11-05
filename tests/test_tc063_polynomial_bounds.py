import unittest

from witnora_core.tc063_theorem_hardening import build_hardening_record, lemma_records


class TC063PolynomialBoundsTest(unittest.TestCase):
    def test_polynomial_bound_lemma(self):
        lemma = {item.lemma_name: item for item in lemma_records()}["Polynomial Bound Lemma"]
        self.assertIn("fixed c", lemma.formal_statement)
        self.assertIn("separator enumeration O(n^c)", lemma.proof_obligations)
        self.assertIn("exponential dependence on c disclosed", lemma.proof_obligations)
        print("TC063_POLYNOMIAL_BOUND_LEMMA_PASS")

    def test_polynomial_bound_summary(self):
        record = build_hardening_record().to_dict()
        poly = record["polynomial_bound_summary"]
        self.assertTrue(poly["fixed_c_polynomiality"])
        self.assertTrue(poly["supported_affine_bound_r_required"])
        self.assertTrue(poly["exponential_dependence_on_c_explicit"])
        self.assertTrue(poly["g5_affine_soundness_dependency"])


if __name__ == "__main__":
    unittest.main()
