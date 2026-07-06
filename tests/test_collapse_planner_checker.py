import unittest

from witnora_core.collapse_planner import (
    COLLAPSE_PLANNER_PLAN_REJECTED,
    COLLAPSE_PLANNER_PLAN_VERIFIED,
    build_collapse_plan_certificate,
    check_collapse_plan_certificate,
    make_planner_instance,
)


class CollapsePlannerCheckerTest(unittest.TestCase):
    def test_checker_accepts_valid_plan(self):
        instance = make_planner_instance("graph_separator_plan")
        cert = build_collapse_plan_certificate(instance)
        result = check_collapse_plan_certificate(instance.formula, cert)
        self.assertEqual(result["status"], COLLAPSE_PLANNER_PLAN_VERIFIED)

    def test_no_fake_execution(self):
        instance = make_planner_instance("fake_execution_claim_reject")
        cert = build_collapse_plan_certificate(instance)
        result = check_collapse_plan_certificate(instance.formula, cert)
        self.assertEqual(result["status"], COLLAPSE_PLANNER_PLAN_REJECTED)
        print("COLLAPSE_PLANNER_NO_FAKE_EXECUTION_PASS")

    def test_no_sat_unsat_claim(self):
        instance = make_planner_instance("fake_sat_unsat_claim_reject")
        cert = build_collapse_plan_certificate(instance)
        result = check_collapse_plan_certificate(instance.formula, cert)
        self.assertEqual(result["status"], COLLAPSE_PLANNER_PLAN_REJECTED)
        print("COLLAPSE_PLANNER_NO_SAT_UNSAT_CLAIM_PASS")

    def test_no_fake_drat(self):
        instance = make_planner_instance("fake_drat_claim_reject")
        cert = build_collapse_plan_certificate(instance)
        result = check_collapse_plan_certificate(instance.formula, cert)
        self.assertEqual(result["status"], COLLAPSE_PLANNER_PLAN_REJECTED)
        print("COLLAPSE_PLANNER_NO_FAKE_DRAT_PASS")

    def test_unknown_operator_rejected(self):
        instance = make_planner_instance("unknown_operator_reject")
        cert = build_collapse_plan_certificate(instance)
        result = check_collapse_plan_certificate(instance.formula, cert)
        self.assertEqual(result["status"], COLLAPSE_PLANNER_PLAN_REJECTED)
        print("COLLAPSE_PLANNER_UNKNOWN_OPERATOR_REJECT_PASS")

    def test_missing_cert_type_rejected(self):
        instance = make_planner_instance("missing_certificate_type_reject")
        cert = build_collapse_plan_certificate(instance)
        result = check_collapse_plan_certificate(instance.formula, cert)
        self.assertEqual(result["status"], COLLAPSE_PLANNER_PLAN_REJECTED)
        print("COLLAPSE_PLANNER_MISSING_CERT_TYPE_REJECT_PASS")

    def test_missing_handoff_rejected(self):
        instance = make_planner_instance("missing_handoff_requirement_reject")
        cert = build_collapse_plan_certificate(instance)
        result = check_collapse_plan_certificate(instance.formula, cert)
        self.assertEqual(result["status"], COLLAPSE_PLANNER_PLAN_REJECTED)
        print("COLLAPSE_PLANNER_MISSING_HANDOFF_REJECT_PASS")


if __name__ == "__main__":
    unittest.main()
