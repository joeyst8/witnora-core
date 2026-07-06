import tempfile
import unittest
from pathlib import Path

from witnora_core.circuit_projection_lift import (
    CIRCUIT_PROJECTION_CERTIFICATE_FAILED,
    check_circuit_projection_certificate,
    make_negative_control,
    run_circuit_projection_lab,
)


class CircuitProjectionControlsTest(unittest.TestCase):
    def test_circuit_projection_fake_drat_reject(self):
        instance, cert = make_negative_control("fake_drat_reject")
        result = check_circuit_projection_certificate(instance.formula, cert)
        self.assertEqual(result["checker_status"], CIRCUIT_PROJECTION_CERTIFICATE_FAILED)
        self.assertIn("FAKE_DRAT_CIRCUIT_PROJECTION_CLAIM", result["errors"])

    def test_circuit_projection_no_completeness_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_circuit_projection_lab(
                instances=["half_adder_sat", "circuit_unsat_control"],
                out_root=Path(tmp) / "g10",
                strict=True,
                zip_path=None,
            )
            root = Path(result["out_root"])
            text = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.json"))
            text += "\n" + (root / "CIRCUIT_PROJECTION_LIFT_REPORT.md").read_text(encoding="utf-8")
        lowered = text.lower()
        self.assertNotIn("circuit projection solves all", lowered)
        self.assertNotIn("full circuit-sat completeness", lowered)
        print("CIRCUIT_PROJECTION_NO_COMPLETENESS_CLAIM_PASS")

    def test_no_theorem_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_circuit_projection_lab(
                instances=["half_adder_sat"],
                out_root=Path(tmp) / "g10",
                strict=True,
                zip_path=None,
            )
            root = Path(result["out_root"])
            report = (root / "CIRCUIT_PROJECTION_LIFT_REPORT.md").read_text(encoding="utf-8").lower()
        self.assertNotIn("strictness theorem", report)
        self.assertNotIn("theorem proven", report)
        print("NO_THEOREM_CLAIM_PASS")

    def test_no_pnp_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_circuit_projection_lab(
                instances=["half_adder_sat"],
                out_root=Path(tmp) / "g10",
                strict=True,
                zip_path=None,
            )
            root = Path(result["out_root"])
            report = (root / "CIRCUIT_PROJECTION_LIFT_REPORT.md").read_text(encoding="utf-8").lower()
        self.assertNotIn("proves p vs np", report)
        self.assertNotIn("p vs np progress", report)
        print("NO_PNP_CLAIM_PASS")

    def test_no_hard_unknown_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_circuit_projection_lab(
                instances=["half_adder_sat", "circuit_unsat_control"],
                out_root=Path(tmp) / "g10",
                strict=True,
                zip_path=None,
            )
            root = Path(result["out_root"])
            text = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.json"))
        self.assertNotIn('"HARD"', text)
        self.assertNotIn('"UNKNOWN"', text)
        print("NO_HARD_UNKNOWN_STATUS_PASS")


if __name__ == "__main__":
    unittest.main()
