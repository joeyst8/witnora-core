import unittest

from witnora_core.claim_boundary import scan_text_for_claim_boundary


class ClaimBoundaryTest(unittest.TestCase):
    def test_forbidden_affirmative_rejected(self):
        result = scan_text_for_claim_boundary("Witnora solves SAT and is ready.")
        self.assertFalse(result["passed"])
        self.assertEqual(result["flagged_phrases"][0]["phrase"], "solves SAT")
        print("CLAIM_BOUNDARY_FORBIDDEN_AFFIRMATIVE_REJECT_PASS")

    def test_negative_context_allowed(self):
        result = scan_text_for_claim_boundary(
            "This release does not claim solves SAT, no parity support, and no P vs NP progress."
        )
        self.assertTrue(result["passed"])
        self.assertGreaterEqual(len(result["findings"]), 2)
        print("CLAIM_BOUNDARY_NEGATIVE_CONTEXT_ALLOW_PASS")


if __name__ == "__main__":
    unittest.main()
