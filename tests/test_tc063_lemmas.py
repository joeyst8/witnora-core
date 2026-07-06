import unittest

from witnora_core.tc063_theorem_hardening import lemma_records


class TC063LemmasTest(unittest.TestCase):
    def setUp(self):
        self.lemmas = {lemma.lemma_name: lemma for lemma in lemma_records()}

    def test_separator_decomposition_lemma(self):
        lemma = self.lemmas["Separator Decomposition Lemma"]
        self.assertIn("residual clause", lemma.formal_statement)
        self.assertIn("residual cross-component clauses rejected", lemma.proof_obligations)
        print("TC063_SEPARATOR_DECOMPOSITION_LEMMA_PASS")

    def test_assignment_exhaustiveness_lemma(self):
        lemma = self.lemmas["Separator Assignment Exhaustiveness Lemma"]
        self.assertIn("exactly one alpha", lemma.formal_statement)
        self.assertIn("all 2^|S| assignments enumerated", lemma.proof_obligations)
        print("TC063_ASSIGNMENT_EXHAUSTIVENESS_LEMMA_PASS")

    def test_affine_component_soundness_lemma(self):
        lemma = self.lemmas["Affine Component Soundness Lemma"]
        self.assertEqual(lemma.status, "PROOF_OBLIGATION_REMAINS")
        self.assertIn("operator_genesis", lemma.dependency_on_modules)
        print("TC063_AFFINE_COMPONENT_SOUNDNESS_LEMMA_PASS")

    def test_sat_lifting_lemma(self):
        lemma = self.lemmas["SAT Lifting Lemma"]
        self.assertIn("original CNF", lemma.formal_statement)
        self.assertIn("final original-CNF witness verification passes", lemma.proof_obligations)
        print("TC063_SAT_LIFTING_LEMMA_PASS")

    def test_unsat_cover_lemma(self):
        lemma = self.lemmas["UNSAT Cover Lemma"]
        self.assertIn("every alpha", lemma.formal_statement)
        self.assertIn("no diagnostic-only component used as proof", lemma.proof_obligations)
        print("TC063_UNSAT_COVER_LEMMA_PASS")

    def test_native_cert_boundary_lemma(self):
        lemma = self.lemmas["Native Certificate Boundary Lemma"]
        self.assertIn("not DRAT/LRAT/FRAT", lemma.formal_statement)
        self.assertIn("no fake DRAT claim", lemma.proof_obligations)
        print("TC063_NATIVE_CERT_BOUNDARY_LEMMA_PASS")

    def test_restricted_scope_lemma(self):
        lemma = self.lemmas["Restricted Scope Lemma"]
        self.assertIn("SAF(c,r)", lemma.formal_statement)
        self.assertIn("fake completeness/P-vs-NP/all-SAT claims rejected", lemma.proof_obligations)
        print("TC063_RESTRICTED_SCOPE_LEMMA_PASS")


if __name__ == "__main__":
    unittest.main()
