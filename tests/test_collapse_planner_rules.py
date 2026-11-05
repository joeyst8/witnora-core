import unittest

from witnora_core.collapse_planner import (
    MISSING_OPERATOR_HYPOTHESIS_PLAN,
    OPERATOR_SEQUENCE_PLAN,
    REVIEW_OR_THEOREMIZATION_PLAN,
    build_collapse_plan_certificate,
    make_planner_instance,
)


class CollapsePlannerRulesTest(unittest.TestCase):
    def _selected(self, instance_id):
        cert = build_collapse_plan_certificate(make_planner_instance(instance_id))
        return next(plan for plan in cert.proposed_plans if plan["plan_id"] == cert.selected_plan_id)

    def test_obstruction_mapping(self):
        plan = self._selected("circuit_projection_plan")
        self.assertIn("CIRCUIT_PROJECTION_SIGNAL", plan["triggering_fingerprints"])
        self.assertEqual(plan["operator_sequence"][0]["operator_name"], "CIRCUIT_PROJECTION_LIFT")
        print("COLLAPSE_PLANNER_OBSTRUCTION_MAPPING_PASS")

    def test_sequence_plan(self):
        plan = self._selected("composed_obstruction_plan")
        self.assertEqual(plan["plan_type"], OPERATOR_SEQUENCE_PLAN)
        self.assertEqual(plan["operator_sequence"][-1]["operator_name"], "COMPOSED_OPERATOR_ORCHESTRATION")
        print("COLLAPSE_PLANNER_SEQUENCE_PLAN_PASS")

    def test_missing_operator_plan(self):
        plan = self._selected("near_affine_missing_operator_plan")
        self.assertEqual(plan["plan_type"], MISSING_OPERATOR_HYPOTHESIS_PLAN)
        self.assertEqual(plan["missing_operator_hypothesis"]["proposed_operator_name"], "ROBUST_AFFINE_COMPLETION_OR_REJECTION")
        print("COLLAPSE_PLANNER_MISSING_OPERATOR_PLAN_PASS")

    def test_review_plan(self):
        plan = self._selected("no_confident_fingerprint_plan")
        self.assertEqual(plan["plan_type"], REVIEW_OR_THEOREMIZATION_PLAN)
        self.assertEqual(plan["missing_operator_hypothesis"]["proposed_operator_name"], "FINGERPRINT_VOCABULARY_EXPANSION")
        print("COLLAPSE_PLANNER_REVIEW_PLAN_PASS")


if __name__ == "__main__":
    unittest.main()
