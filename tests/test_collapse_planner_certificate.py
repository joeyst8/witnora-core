import unittest

from witnora_core.collapse_planner import (
    COLLAPSE_PLANNER_PLAN_VERIFIED,
    EXECUTION_REQUIRED,
    FINITE_PLANNER_CERTIFICATE_VERIFIED,
    G12_GRAMMAR,
    build_collapse_plan_certificate,
    check_collapse_plan_certificate,
    make_planner_instance,
    operator_portfolio,
)


class CollapsePlannerCertificateTest(unittest.TestCase):
    def test_collapse_planner_cert_schema(self):
        instance = make_planner_instance("composed_obstruction_plan")
        cert = build_collapse_plan_certificate(instance)
        data = cert.to_dict()
        self.assertEqual(data["type"], "COLLAPSE_PLAN_CERTIFICATE")
        self.assertEqual(data["evidence_grade"], FINITE_PLANNER_CERTIFICATE_VERIFIED)
        self.assertEqual(data["execution_status"], EXECUTION_REQUIRED)
        self.assertIn("source_obstruction_record", data)
        self.assertIn("available_operators", data)
        self.assertIn("proposed_plans", data)
        self.assertIn("expected_certificate_chain", data)
        self.assertEqual(check_collapse_plan_certificate(instance.formula, cert)["status"], COLLAPSE_PLANNER_PLAN_VERIFIED)
        print("COLLAPSE_PLANNER_CERT_SCHEMA_PASS")

    def test_operator_portfolio(self):
        names = {item.operator_name for item in operator_portfolio()}
        self.assertIn("CIRCUIT_PROJECTION_LIFT", names)
        self.assertIn("PROOF_MOTIF_GENERALIZATION_CHECKER", names)
        self.assertNotIn("G7_OBSTRUCTION_DUAL_CERTIFICATE_PROTOTYPE", names)
        print("COLLAPSE_PLANNER_OPERATOR_PORTFOLIO_PASS")

    def test_execution_required_and_g12_status(self):
        instance = make_planner_instance("circuit_projection_plan")
        cert = build_collapse_plan_certificate(instance)
        self.assertEqual(cert.execution_status, EXECUTION_REQUIRED)
        self.assertEqual(cert.evidence_grade, FINITE_PLANNER_CERTIFICATE_VERIFIED)
        self.assertIn(G12_GRAMMAR, {G12_GRAMMAR})
        print("COLLAPSE_PLANNER_EXECUTION_REQUIRED_PASS")


if __name__ == "__main__":
    unittest.main()
