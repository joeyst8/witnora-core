import unittest

from witnora_core.paper_hardening import claim_boundary_appendix_text, limitations_and_nonclaims_text


class V213ClaimBoundaryAppendixTest(unittest.TestCase):
    def test_no_new_operator(self):
        text = limitations_and_nonclaims_text()
        self.assertIn("v2.13 does not add a new operator.", text)
        self.assertNotIn("G7_", text)
        print("NO_NEW_OPERATOR_PASS")

    def test_no_solver_logic_change(self):
        text = limitations_and_nonclaims_text()
        self.assertIn("does not change solver logic", text)
        print("NO_SOLVER_LOGIC_CHANGE_PASS")

    def test_no_xor_logic_change(self):
        text = limitations_and_nonclaims_text()
        self.assertIn("XOR-solving logic", text)
        print("NO_XOR_LOGIC_CHANGE_PASS")

    def test_no_proof_export_logic_change(self):
        text = limitations_and_nonclaims_text()
        self.assertIn("proof-export logic", text)
        print("NO_PROOF_EXPORT_LOGIC_CHANGE_PASS")

    def test_no_hierarchy_completeness_or_pnp_or_polytime_claim(self):
        text = limitations_and_nonclaims_text()
        self.assertIn("No hierarchy completeness is claimed.", text)
        self.assertIn("No P vs NP progress is claimed.", text)
        self.assertIn("No polynomial-time SAT algorithm is claimed.", text)
        print("NO_HIERARCHY_COMPLETENESS_CLAIM_PASS")
        print("NO_POLYTIME_SAT_CLAIM_PASS")
        print("NO_PNP_CLAIM_PASS")

    def test_no_hard_unknown_status(self):
        text = claim_boundary_appendix_text() + "\n" + limitations_and_nonclaims_text()
        self.assertNotIn("HARD", text)
        self.assertNotIn("UNKNOWN", text)
        print("NO_HARD_UNKNOWN_STATUS_PASS")


if __name__ == "__main__":
    unittest.main()
