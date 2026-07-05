import tempfile
import unittest
from pathlib import Path

from witnora_core.collapse_theory import (
    PIGEONHOLE_CERTIFICATE_VERIFIED,
    UNSAT_PIGEONHOLE_NATIVE_CERTIFIED,
    run_pigeonhole_lab,
)


class PigeonholeG3OperatorTest(unittest.TestCase):
    def test_g3_operator_delta(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_pigeonhole_lab(instances=["php_3_2", "php_4_3", "php_5_4"], out_root=Path(tmp) / "lab")
            report = (Path(tmp) / "lab" / "PIGEONHOLE_CARDINALITY_COLLAPSE_REPORT.md").read_text(encoding="utf-8")
        delta = result["g3_operator_delta_summary"]
        self.assertEqual(delta["g3_native_certified"], 3)
        self.assertEqual(delta["fake_drat_claims"], 0)
        self.assertIn("not a complete PB solver", report)
        print("G3_OPERATOR_DELTA_PASS")

    def test_g3_strictness_not_theorem(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_pigeonhole_lab(instances=["php_3_2"], out_root=Path(tmp) / "lab")
            report = (Path(tmp) / "lab" / "PIGEONHOLE_CARDINALITY_COLLAPSE_REPORT.md").read_text(encoding="utf-8")
        self.assertEqual(result["g3_operator_delta_summary"]["strictness_status"], "EMPIRICAL_EVIDENCE_NOT_THEOREM")
        self.assertIn("not claim", report)
        self.assertIn("G3 strictness theorem", report)
        print("G3_STRICTNESS_NOT_THEOREM_PASS")

    def test_php_6_5_optional_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_pigeonhole_lab(instances=["php_6_5"], out_root=Path(tmp) / "lab")
        row = result["pigeonhole_native_unsat_summary"][0]
        self.assertEqual(row["checker_status"], PIGEONHOLE_CERTIFICATE_VERIFIED)
        self.assertEqual(row["g3_public_category"], UNSAT_PIGEONHOLE_NATIVE_CERTIFIED)


if __name__ == "__main__":
    unittest.main()
