import json
import tempfile
import unittest
from pathlib import Path

from witnora_core.finite_edge_certificate import build_outputs


class FiniteEdgeDeltaReportsTest(unittest.TestCase):
    def test_finite_edge_delta_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "edge"
            result = build_outputs(instances=["cycle_4_3color", "cycle_6_3color"], out_root=root, zip_path="")
            report = (root / "FINITE_EDGE_DELTA_G1_G2_REPORT.md").read_text(encoding="utf-8")
            boundary = json.loads((root / "edge_delta_claim_boundary.json").read_text(encoding="utf-8"))
        self.assertIn("FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED", report)
        self.assertIn("not a lower-bound strictness theorem", report)
        self.assertFalse(boundary["lower_replay_is_lower_bound"])
        self.assertEqual(result["finite_edge_delta_checker_result"]["checker_status"], "FINITE_EDGE_DELTA_CERTIFICATE_VERIFIED")
        print("FINITE_EDGE_DELTA_REPORT_PASS")

    def test_paper_edge_delta_section(self):
        paper = Path("paper/WITNORA_COLLAPSE_HIERARCHY_DRAFT.md").read_text(encoding="utf-8")
        self.assertIn("Finite Empirical Edge Delta Certificate", paper)
        self.assertIn("not a lower-bound strictness theorem", paper)
        self.assertIn("does not prove G1_XOR is strictly weaker than G2_SYMMETRY_CERTIFIED", paper)
        print("PAPER_EDGE_DELTA_SECTION_PASS")


if __name__ == "__main__":
    unittest.main()
