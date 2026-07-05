import tempfile
import unittest
from pathlib import Path

from witnora_core.collapse_theory import run_pigeonhole_lab


class SymmetryCardinalityIntegrationTest(unittest.TestCase):
    def test_symmetry_cardinality_integration(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_pigeonhole_lab(instances=["php_4_3"], out_root=Path(tmp) / "lab")
        row = result["symmetry_cardinality_integration"][0]
        self.assertIn("Symmetry helps", row["integration_claim"])
        self.assertIn("native counting certifies UNSAT", row["integration_claim"])
        print("SYMMETRY_CARDINALITY_INTEGRATION_PASS")

    def test_cardinality_no_fake_pb_solver(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_pigeonhole_lab(instances=["php_3_2"], out_root=Path(tmp) / "lab")
        trace = result["pigeonhole_certificates"][0]["cardinality_detection_trace"]
        self.assertEqual(trace["pb_solver_claim"], "NO_PB_SOLVING_CLAIM")
        print("CARDINALITY_NO_FAKE_PB_SOLVER_PASS")

    def test_no_pnp_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "lab"
            run_pigeonhole_lab(instances=["php_3_2"], out_root=root)
            text = (root / "PIGEONHOLE_CARDINALITY_COLLAPSE_REPORT.md").read_text(encoding="utf-8")
        self.assertIn("does not claim P vs NP progress", text)
        self.assertNotIn("proves P vs NP", text)
        print("NO_PNP_CLAIM_PASS")

    def test_no_hard_unknown_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "lab"
            run_pigeonhole_lab(instances=["php_3_2"], out_root=root)
            payload = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.json"))
        self.assertNotIn('"HARD"', payload)
        self.assertNotIn('"UNKNOWN"', payload)
        print("NO_HARD_UNKNOWN_STATUS_PASS")


if __name__ == "__main__":
    unittest.main()
