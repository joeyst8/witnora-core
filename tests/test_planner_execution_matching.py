import unittest

from witnora_core.planner_execution import (
    PLANNER_EXECUTION_CERTIFICATE_FAILED,
    build_planner_execution_certificate,
    check_planner_execution_certificate,
    make_planner_execution_instance,
)


class PlannerExecutionMatchingTest(unittest.TestCase):
    def _rejects(self, instance_id):
        instance = make_planner_execution_instance(instance_id)
        cert, plan = build_planner_execution_certificate(instance)
        result = check_planner_execution_certificate(instance.formula, plan, cert)
        self.assertEqual(result["checker_status"], PLANNER_EXECUTION_CERTIFICATE_FAILED)
        return result

    def test_no_fake_execution_sat_unsat_drat(self):
        self.assertIn("FAKE_EXECUTION_RECORD", self._rejects("fake_execution_record_reject")["errors"])
        print("PLANNER_EXECUTION_NO_FAKE_EXECUTION_PASS")
        self.assertTrue(any("SAT_" in err or "WITNESS" in err for err in self._rejects("fake_sat_unsat_result_reject")["errors"]))
        print("PLANNER_EXECUTION_NO_FAKE_SAT_UNSAT_PASS")
        self.assertIn("FAKE_DRAT_EXECUTION_CLAIM", self._rejects("fake_drat_execution_reject")["errors"])
        print("PLANNER_EXECUTION_NO_FAKE_DRAT_PASS")

    def test_step_and_handoff_rejections(self):
        self.assertTrue(any("ACTUAL_STEP" in err for err in self._rejects("unchecked_step_certificate_reject")["errors"]))
        print("PLANNER_EXECUTION_UNCHECKED_STEP_REJECT_PASS")
        self.assertTrue(any("HANDOFF" in err for err in self._rejects("bad_handoff_reject")["errors"]))
        print("PLANNER_EXECUTION_BAD_HANDOFF_REJECT_PASS")
        self.assertTrue(any("CERTIFICATE_MISSING" in err for err in self._rejects("missing_actual_certificate_reject")["errors"]))
        print("PLANNER_EXECUTION_MISSING_CERT_REJECT_PASS")

    def test_result_obligation_rejections(self):
        self.assertIn("DIAGNOSTIC_STEP_USED_AS_RESULT", self._rejects("diagnostic_step_as_result_reject")["errors"])
        print("PLANNER_EXECUTION_DIAGNOSTIC_AS_RESULT_REJECT_PASS")
        self.assertTrue(any("SAT_" in err or "WITNESS" in err for err in self._rejects("bad_witness_original_cnf_reject")["errors"]))
        print("PLANNER_EXECUTION_BAD_WITNESS_REJECT_PASS")
        self.assertIn("UNSAT_STEP_WITHOUT_PRESERVATION", self._rejects("unsat_without_preservation_reject")["errors"])
        print("PLANNER_EXECUTION_UNSAT_NO_PRESERVATION_REJECT_PASS")

    def test_plan_and_operator_rejections(self):
        self.assertIn("PLAN_CERTIFICATE_NOT_VERIFIED", self._rejects("plan_hash_tamper_reject")["errors"])
        print("PLANNER_EXECUTION_PLAN_TAMPER_REJECT_PASS")
        self.assertTrue(any(err.startswith("UNKNOWN_OPERATOR") for err in self._rejects("unknown_operator_execution_reject")["errors"]))
        print("PLANNER_EXECUTION_UNKNOWN_OPERATOR_REJECT_PASS")
        self.assertTrue(any("FORBIDDEN_STATUS" in err for err in self._rejects("hard_unknown_status_reject")["errors"]))
        print("PLANNER_EXECUTION_HARD_UNKNOWN_REJECT_PASS")


if __name__ == "__main__":
    unittest.main()
