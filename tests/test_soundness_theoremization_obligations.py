import unittest

from witnora_core.soundness_theoremization import OBLIGATION_CATEGORIES, build_theoremization_record


class SoundnessTheoremizationObligationsTest(unittest.TestCase):
    def setUp(self):
        self.record = build_theoremization_record().to_dict()

    def test_proof_obligation_matrix(self):
        matrix = self.record["proof_obligation_matrix"]
        self.assertEqual(len(matrix), len(self.record["theorem_candidates"]) * len(OBLIGATION_CATEGORIES))
        categories = {row["obligation_category"] for row in matrix}
        self.assertEqual(categories, set(OBLIGATION_CATEGORIES))
        self.assertTrue(any(row["risk_level"] == "HIGH" for row in matrix))
        self.assertTrue(all(row["still_informal"] for row in matrix))
        print("PROOF_OBLIGATION_MATRIX_PASS")

    def test_claim_boundary_audit(self):
        audit = self.record["claim_boundary_audit"]
        self.assertGreaterEqual(len(audit), 6)
        forbidden = " ".join(row["forbidden_wording"] for row in audit)
        self.assertIn("Theorem proven", forbidden)
        self.assertIn("P vs NP progress", forbidden)
        self.assertIn("HARD or UNKNOWN", forbidden)
        print("CLAIM_BOUNDARY_AUDIT_PASS")

    def test_reviewer_objection_table(self):
        objections = self.record["reviewer_objection_table"]
        self.assertGreaterEqual(len(objections), 7)
        text = "\n".join(row["objection"] + " " + row["response"] for row in objections)
        self.assertIn("Plans are not proofs", text)
        self.assertIn("Native certificates are not external proofs", text)
        self.assertIn("Projection may be unsound", text)
        print("REVIEWER_OBJECTION_TABLE_PASS")


if __name__ == "__main__":
    unittest.main()
