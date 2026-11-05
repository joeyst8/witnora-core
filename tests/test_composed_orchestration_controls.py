import tempfile
import unittest
from pathlib import Path

from witnora_core.composed_orchestration import (
    COMPOSED_ORCHESTRATION_CERTIFICATE_FAILED,
    check_composed_orchestration_certificate,
    make_negative_control,
    run_composed_orchestration_lab,
)


class ComposedOrchestrationControlsTest(unittest.TestCase):
    def test_composed_orchestration_missing_step_certificate_reject(self):
        instance, cert = make_negative_control("missing_step_certificate_reject")
        result = check_composed_orchestration_certificate(instance.formula, cert)
        self.assertEqual(result["checker_status"], COMPOSED_ORCHESTRATION_CERTIFICATE_FAILED)
        self.assertTrue(any("MISSING_STEP_CERTIFICATE" in error for error in result["errors"]))

    def test_no_theorem_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_composed_orchestration_lab(
                instances=["composed_sat_lift", "composed_unsat_cover"],
                out_root=Path(tmp) / "g9",
                strict=True,
                zip_path=None,
            )
            root = Path(result["out_root"])
            text = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.json"))
            text += "\n" + (root / "COMPOSED_ORCHESTRATION_REPORT.md").read_text(encoding="utf-8")
        self.assertNotIn("strictness theorem", text.lower())
        self.assertNotIn("theorem proven", text.lower())
        print("NO_THEOREM_CLAIM_PASS")

    def test_no_completeness_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_composed_orchestration_lab(
                instances=["composed_sat_lift", "composed_unsat_cover"],
                out_root=Path(tmp) / "g9",
                strict=True,
                zip_path=None,
            )
            root = Path(result["out_root"])
            report = (root / "COMPOSED_ORCHESTRATION_REPORT.md").read_text(encoding="utf-8").lower()
        self.assertNotIn("universal collapse path", report)
        self.assertNotIn("orchestration solves all", report)
        print("NO_COMPLETENESS_CLAIM_PASS")

    def test_no_pnp_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_composed_orchestration_lab(
                instances=["composed_sat_lift"],
                out_root=Path(tmp) / "g9",
                strict=True,
                zip_path=None,
            )
            root = Path(result["out_root"])
            report = (root / "COMPOSED_ORCHESTRATION_REPORT.md").read_text(encoding="utf-8").lower()
        self.assertNotIn("proves p vs np", report)
        self.assertNotIn("p vs np progress", report)
        print("NO_PNP_CLAIM_PASS")

    def test_no_hard_unknown_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_composed_orchestration_lab(
                instances=["composed_sat_lift", "composed_unsat_cover"],
                out_root=Path(tmp) / "g9",
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
