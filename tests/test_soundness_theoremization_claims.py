import unittest

from witnora_core.soundness_theoremization import FORBIDDEN_STATUS_VALUES, build_theoremization_record


class SoundnessTheoremizationClaimsTest(unittest.TestCase):
    def setUp(self):
        self.record = build_theoremization_record().to_dict()

    def test_no_theorem_proven_claim(self):
        for candidate in self.record["theorem_candidates"]:
            self.assertTrue(candidate["may_not_be_claimed_as_proven"])
            self.assertNotIn(candidate["status"], {"THEOREM_PROVEN", "PROVEN", "COMPLETE"})
        print("NO_THEOREM_PROVEN_CLAIM_PASS")

    def test_no_completeness_or_pnp_claim(self):
        joined_nonclaims = "\n".join(
            "\n".join(candidate["nonclaims"]) for candidate in self.record["theorem_candidates"]
        ).lower()
        self.assertIn("does not claim p vs np progress", joined_nonclaims)
        self.assertIn("does not claim", joined_nonclaims)
        for candidate in self.record["theorem_candidates"]:
            self.assertNotEqual(candidate["status"], "PNP_PROGRESS")
        print("NO_COMPLETENESS_CLAIM_PASS")
        print("NO_PNP_CLAIM_PASS")

    def test_no_fake_drat_claim(self):
        audit = self.record["claim_boundary_audit"]
        native_rows = [row for row in audit if "Native" in row["allowed_wording"] or "native" in row["reason"]]
        self.assertTrue(native_rows)
        self.assertTrue(any("DRAT" in row["forbidden_wording"] for row in audit))
        print("NO_FAKE_DRAT_CLAIM_PASS")

    def test_no_hard_unknown_status(self):
        statuses = {self.record["status"], self.record["public_category"]}
        statuses.update(candidate["status"] for candidate in self.record["theorem_candidates"])
        statuses.update(row["current_status"] for row in self.record["proof_obligation_matrix"])
        self.assertFalse(statuses & FORBIDDEN_STATUS_VALUES)
        print("NO_HARD_UNKNOWN_STATUS_PASS")


if __name__ == "__main__":
    unittest.main()
