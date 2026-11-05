import unittest

from witnora_core.collapse_planner import (
    COLLAPSE_PLANNER_PLAN_REJECTED,
    build_collapse_plan_certificate,
    check_collapse_plan_certificate,
    make_planner_instance,
)


class CollapsePlannerControlsTest(unittest.TestCase):
    def test_diagnostic_as_proof_rejected(self):
        instance = make_planner_instance("diagnostic_step_as_proof_reject")
        cert = build_collapse_plan_certificate(instance)
        result = check_collapse_plan_certificate(instance.formula, cert)
        self.assertEqual(result["status"], COLLAPSE_PLANNER_PLAN_REJECTED)
        print("COLLAPSE_PLANNER_DIAGNOSTIC_AS_PROOF_REJECT_PASS")

    def test_hard_unknown_rejected(self):
        instance = make_planner_instance("hard_unknown_status_reject")
        cert = build_collapse_plan_certificate(instance)
        result = check_collapse_plan_certificate(instance.formula, cert)
        self.assertEqual(result["status"], COLLAPSE_PLANNER_PLAN_REJECTED)
        print("COLLAPSE_PLANNER_HARD_UNKNOWN_REJECT_PASS")

    def test_missing_unsat_preservation_rejected(self):
        instance = make_planner_instance("missing_unsat_preservation_requirement_reject")
        cert = build_collapse_plan_certificate(instance)
        result = check_collapse_plan_certificate(instance.formula, cert)
        self.assertEqual(result["status"], COLLAPSE_PLANNER_PLAN_REJECTED)

    def test_no_forbidden_claims(self):
        instance = make_planner_instance("composed_obstruction_plan")
        cert = build_collapse_plan_certificate(instance)
        text = str(cert.to_dict()).lower()
        self.assertNotIn("theorem proven", text)
        self.assertNotIn("hierarchy completeness", text)
        self.assertNotIn("p vs np progress", text)
        self.assertNotIn("hard'", text)
        self.assertNotIn("unknown'", text)
        print("NO_THEOREM_CLAIM_PASS")
        print("NO_COMPLETENESS_CLAIM_PASS")
        print("NO_PNP_CLAIM_PASS")
        print("NO_HARD_UNKNOWN_STATUS_PASS")


if __name__ == "__main__":
    unittest.main()
