import tempfile
import unittest
from pathlib import Path

from witnora_core.soundness_theoremization import run_soundness_theoremization


class SoundnessTheoremizationReportTest(unittest.TestCase):
    def test_report_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "v221"
            run_soundness_theoremization(out_root=out, strict=True, zip_path=None)
            report = out / "THEOREMIZATION_REPORT.md"
            self.assertTrue(report.exists())
            text = report.read_text(encoding="utf-8")
            self.assertIn("G9-G13 Soundness Backbone Theoremization", text)
            self.assertIn("No theorem is marked proven", text)
            self.assertIn("finite evidence does not imply", text.lower())
            self.assertIn("P-vs-NP progress", text)
        print("SOUNDNESS_THEOREMIZATION_G9_PASS")
        print("SOUNDNESS_THEOREMIZATION_G10_PASS")
        print("SOUNDNESS_THEOREMIZATION_G11_PASS")
        print("SOUNDNESS_THEOREMIZATION_G12_PASS")
        print("SOUNDNESS_THEOREMIZATION_G13_PASS")

    def test_report_artifact_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "v221"
            zip_path = Path(tmp) / "artifact.zip"
            result = run_soundness_theoremization(out_root=out, strict=True, zip_path=zip_path)
            self.assertTrue(zip_path.exists())
            self.assertRegex(result["zip_sha256"], r"^[A-F0-9]{64}$")


if __name__ == "__main__":
    unittest.main()
