import tempfile
import unittest
from pathlib import Path

from witnora_core.collapse_planner import (
    FINITE_PLANNER_CERTIFICATE_VERIFIED,
    G12_GRAMMAR,
    run_collapse_planner_lab,
)


class CollapsePlannerG12Test(unittest.TestCase):
    def test_g12_planner_delta(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        result = run_collapse_planner_lab(
            instances=[
                "composed_obstruction_plan",
                "circuit_projection_plan",
                "proof_motif_near_plan",
                "graph_separator_plan",
                "near_affine_missing_operator_plan",
                "no_confident_fingerprint_plan",
            ],
            out_root=Path(tmp.name) / "g12",
            strict=True,
            zip_path=None,
        )
        summary = result["g12_planner_delta_summary"]
        self.assertEqual(summary["operator_added"], G12_GRAMMAR)
        self.assertEqual(summary["evidence_grade"], FINITE_PLANNER_CERTIFICATE_VERIFIED)
        self.assertEqual(summary["planner_delta_count"], 6)
        self.assertTrue(summary["execution_required"])
        print("G12_PLANNER_DELTA_PASS")


if __name__ == "__main__":
    unittest.main()
