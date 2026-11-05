import unittest

from witnora_core.tc063_theorem_hardening import run_scaling_evidence


class TC063ScalingTest(unittest.TestCase):
    def test_n64_and_n128_scaling(self):
        scaling = run_scaling_evidence()
        rows = {(row["family"], row["n"]): row for row in scaling["rows"]}
        for family in ["saf_sat_chain", "saf_unsat_cover", "saf_balanced_sat"]:
            self.assertEqual(rows[(family, 64)]["checker_status"], "SEPARATOR_AFFINE_CERTIFICATE_VERIFIED")
            self.assertEqual(rows[(family, 128)]["checker_status"], "SEPARATOR_AFFINE_CERTIFICATE_VERIFIED")
        print("TC063_N64_PASS")
        print("TC063_N128_PASS")

    def test_scaling_evidence_not_proof(self):
        scaling = run_scaling_evidence()
        self.assertIn("support implementation only", scaling["evidence_boundary"])
        self.assertEqual(scaling["passed"], scaling["total"])
        print("TC063_SCALING_EVIDENCE_NOT_PROOF_PASS")


if __name__ == "__main__":
    unittest.main()
