import unittest

from witnora_core.submit_release_finalize_v226 import (
    final_forbidden_claim_scan,
    final_preprint_text,
)


class FinalClaimsV226Test(unittest.TestCase):
    def test_forbidden_claim_scan_passes(self):
        scan = final_forbidden_claim_scan([final_preprint_text()], [])
        self.assertEqual(scan["verification_status"], "PASS")
        self.assertEqual(scan["hit_count"], 0)
        print("FINAL_FORBIDDEN_CLAIM_SCAN_PASS")

    def test_forbidden_claim_scan_rejects_bad_text(self):
        scan = final_forbidden_claim_scan(["We solved P vs NP and finite tests replace proof."], [])
        self.assertEqual(scan["verification_status"], "FAIL")

    def test_final_nonclaims(self):
        text = final_preprint_text()
        for forbidden in [
            "we solved P vs NP",
            "all-SAT coverage is claimed",
            "hierarchy completeness is claimed",
            "TC-063 is fully proven",
            "DRAT proof claimed",
        ]:
            self.assertNotIn(forbidden, text)
        print("FINAL_NO_PNP_CLAIM_PASS")
        print("FINAL_NO_ALL_SAT_CLAIM_PASS")
        print("FINAL_NO_COMPLETENESS_CLAIM_PASS")
        print("FINAL_NO_THEOREM_PROVEN_UNQUALIFIED_PASS")
        print("FINAL_NO_FAKE_DRAT_LRAT_FRAT_PASS")
        print("FINAL_NO_HARD_UNKNOWN_STATUS_PASS")


if __name__ == "__main__":
    unittest.main()
