import unittest

from witnora_core.planner_execution import (
    DIAGNOSTIC_ONLY,
    EXECUTION_FAILED,
    MATCH,
    MISMATCH,
    PARTIAL_MATCH,
    PLANNER_EXECUTION_CERTIFICATE_VERIFIED,
    PLANNER_EXECUTION_DIAGNOSTIC_ONLY,
    PLANNER_EXECUTION_MATCH_VERIFIED,
    PLANNER_EXECUTION_MISMATCH_VERIFIED,
    SAT_CERTIFIED,
    UNSAT_CERTIFIED,
    build_planner_execution_certificate,
    check_planner_execution_certificate,
    make_planner_execution_instance,
)


class PlannerExecutionCheckerTest(unittest.TestCase):
    def _checked(self, instance_id):
        instance = make_planner_execution_instance(instance_id)
        cert, plan = build_planner_execution_certificate(instance)
        return cert.to_dict(), check_planner_execution_certificate(instance.formula, plan, cert)

    def test_match_and_mismatch(self):
        cert, result = self._checked("projected_affine_plan_execution")
        self.assertEqual(cert["comparison"]["comparison_status"], MATCH)
        self.assertEqual(result["status"], PLANNER_EXECUTION_MATCH_VERIFIED)
        print("PLANNER_EXECUTION_MATCH_PASS")
        cert, result = self._checked("mismatch_control")
        self.assertEqual(cert["comparison"]["comparison_status"], MISMATCH)
        self.assertEqual(result["status"], PLANNER_EXECUTION_MISMATCH_VERIFIED)
        print("PLANNER_EXECUTION_MISMATCH_PASS")

    def test_failed_execution_no_result(self):
        cert, result = self._checked("failed_execution_control")
        self.assertEqual(result["checker_status"], PLANNER_EXECUTION_CERTIFICATE_VERIFIED)
        self.assertEqual(result["status"], PLANNER_EXECUTION_DIAGNOSTIC_ONLY)
        self.assertEqual(cert["execution_result"]["result_type"], EXECUTION_FAILED)
        self.assertFalse(cert["execution_result"]["verified_against_original_cnf"])
        print("PLANNER_EXECUTION_FAILED_NO_RESULT_PASS")

    def test_sat_original_cnf(self):
        cert, result = self._checked("projected_affine_plan_execution")
        self.assertEqual(result["execution_result_type"], SAT_CERTIFIED)
        self.assertTrue(cert["execution_result"]["verified_against_original_cnf"])
        self.assertEqual(cert["witness_or_unsat_trace"]["original_cnf_verification_status"], "SAT_WITNESS_VERIFIED_AGAINST_ORIGINAL_CNF")
        print("PLANNER_EXECUTION_SAT_ORIGINAL_CNF_PASS")

    def test_unsat_preservation(self):
        cert, result = self._checked("proof_motif_plan_execution")
        self.assertEqual(result["execution_result_type"], UNSAT_CERTIFIED)
        self.assertEqual(result["status"], PLANNER_EXECUTION_MATCH_VERIFIED)
        self.assertTrue(all(row["verified"] for row in cert["witness_or_unsat_trace"]["unsat_preservation_trace"]))
        print("PLANNER_EXECUTION_UNSAT_PRESERVATION_PASS")

    def test_partial_match_is_conservative(self):
        cert, result = self._checked("circuit_plan_execution")
        self.assertEqual(cert["comparison"]["comparison_status"], PARTIAL_MATCH)
        self.assertEqual(result["status"], PLANNER_EXECUTION_MISMATCH_VERIFIED)
        self.assertEqual(cert["public_category"], "PLANNER_EXECUTION_DIAGNOSTIC_ONLY")


if __name__ == "__main__":
    unittest.main()
