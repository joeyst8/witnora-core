import unittest

from witnora_core.planner_execution import (
    build_planner_execution_certificate,
    make_planner_execution_instance,
)


class PlannerExecutionControlsTest(unittest.TestCase):
    def test_claim_boundaries(self):
        instance = make_planner_execution_instance("projected_affine_plan_execution")
        cert, _plan = build_planner_execution_certificate(instance)
        payload = str(cert.to_dict()).lower()
        self.assertIn("no theorem", payload)
        self.assertIn("p-vs-np claim", payload)
        self.assertNotIn("theorem proven", payload)
        self.assertNotIn("hierarchy completeness", payload)
        self.assertNotIn("p vs np progress", payload)
        print("NO_THEOREM_CLAIM_PASS")
        print("NO_COMPLETENESS_CLAIM_PASS")
        print("NO_PNP_CLAIM_PASS")

    def test_no_hard_unknown_status(self):
        for instance_id in [
            "projected_affine_plan_execution",
            "proof_motif_plan_execution",
            "mismatch_control",
            "failed_execution_control",
        ]:
            instance = make_planner_execution_instance(instance_id)
            cert, _plan = build_planner_execution_certificate(instance)
            payload = str(cert.to_dict())
            self.assertNotIn("'HARD'", payload)
            self.assertNotIn("'UNKNOWN'", payload)
        print("NO_HARD_UNKNOWN_STATUS_PASS")


if __name__ == "__main__":
    unittest.main()
