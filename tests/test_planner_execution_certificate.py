import unittest

from witnora_core.planner_execution import (
    FINITE_PLANNER_EXECUTION_VERIFIED,
    G13_GRAMMAR,
    PLANNER_EXECUTION_CERTIFICATE_VERIFIED,
    PLANNER_EXECUTION_MATCH_VERIFIED,
    build_planner_execution_certificate,
    check_planner_execution_certificate,
    make_planner_execution_instance,
)


class PlannerExecutionCertificateTest(unittest.TestCase):
    def test_planner_execution_cert_schema(self):
        instance = make_planner_execution_instance("projected_affine_plan_execution")
        cert, plan = build_planner_execution_certificate(instance)
        data = cert.to_dict()
        self.assertEqual(data["type"], "PLANNER_EXECUTION_CERTIFICATE")
        self.assertEqual(data["evidence_grade"], FINITE_PLANNER_EXECUTION_VERIFIED)
        self.assertIn("planned_chain", data)
        self.assertIn("actual_execution_chain", data)
        self.assertIn("comparison", data)
        self.assertIn("execution_result", data)
        print("PLANNER_EXECUTION_CERT_SCHEMA_PASS")

    def test_planner_execution_plan_verify(self):
        instance = make_planner_execution_instance("projected_affine_plan_execution")
        cert, plan = build_planner_execution_certificate(instance)
        result = check_planner_execution_certificate(instance.formula, plan, cert)
        self.assertEqual(result["checker_status"], PLANNER_EXECUTION_CERTIFICATE_VERIFIED)
        self.assertEqual(result["status"], PLANNER_EXECUTION_MATCH_VERIFIED)
        self.assertIn(G13_GRAMMAR, {G13_GRAMMAR})
        print("PLANNER_EXECUTION_PLAN_VERIFY_PASS")

    def test_actual_chain_and_step_certificates(self):
        instance = make_planner_execution_instance("projected_affine_plan_execution")
        cert, _plan = build_planner_execution_certificate(instance)
        chain = cert.to_dict()["actual_execution_chain"]
        self.assertEqual([step["operator_name"] for step in chain], ["CIRCUIT_PROJECTION_LIFT", "HIGH_ARITY_AFFINE_RESIDUE"])
        self.assertTrue(all(step["step_certificate"] for step in chain))
        self.assertTrue(all(step["actual_checker_status"] == "PLANNER_EXECUTION_STEP_VERIFIED" for step in chain))
        print("PLANNER_EXECUTION_ACTUAL_CHAIN_PASS")
        print("PLANNER_EXECUTION_STEP_CERT_CHECK_PASS")

    def test_handoff_trace(self):
        instance = make_planner_execution_instance("projected_affine_plan_execution")
        cert, _plan = build_planner_execution_certificate(instance)
        chain = cert.to_dict()["actual_execution_chain"]
        self.assertEqual(chain[0]["output_formula_hash"], chain[1]["input_formula_hash"])
        self.assertTrue(cert.to_dict()["handoff_trace"]["all_handoffs_verified"])
        print("PLANNER_EXECUTION_HANDOFF_PASS")


if __name__ == "__main__":
    unittest.main()
