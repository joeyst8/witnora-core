import tempfile
import unittest
from pathlib import Path

from witnora_core.planner_execution import (
    FINITE_PLANNER_EXECUTION_VERIFIED,
    G13_GRAMMAR,
    run_planner_execution_lab,
)


class PlannerExecutionG13Test(unittest.TestCase):
    def test_g13_planner_execution_delta(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_planner_execution_lab(
                instances=[
                    "projected_affine_plan_execution",
                    "circuit_plan_execution",
                    "proof_motif_plan_execution",
                    "graph_separator_plan_execution",
                    "composed_plan_execution",
                    "mismatch_control",
                    "failed_execution_control",
                ],
                out_root=Path(tmp) / "g13",
                strict=True,
            )
        delta = result["g13_planner_execution_delta_summary"]
        self.assertEqual(delta["operator_added"], G13_GRAMMAR)
        self.assertEqual(delta["evidence_grade"], FINITE_PLANNER_EXECUTION_VERIFIED)
        self.assertGreaterEqual(delta["match_count"], 1)
        self.assertGreaterEqual(delta["mismatch_or_partial_count"], 1)
        self.assertGreaterEqual(delta["sat_certified_count"], 1)
        self.assertGreaterEqual(delta["unsat_certified_count"], 1)
        print("G13_PLANNER_EXECUTION_DELTA_PASS")

    def test_reports_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "g13"
            run_planner_execution_lab(
                instances=["projected_affine_plan_execution", "mismatch_control"],
                out_root=out,
                strict=True,
            )
            self.assertTrue((out / "PLANNER_GUIDED_EXECUTION_REPORT.md").exists())
            self.assertTrue((out / "planner_execution_certificates.json").exists())
            self.assertTrue((out / "plan_vs_execution_comparison.json").exists())


if __name__ == "__main__":
    unittest.main()
