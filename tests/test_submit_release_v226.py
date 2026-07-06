import tempfile
import unittest
from pathlib import Path

from witnora_core.submit_release_finalize_v226 import (
    PACKAGE_ID,
    PACKAGE_VERSION,
    PREPRINT_TITLE,
    final_preprint_text,
    run_submit_release_package,
)


class SubmitReleaseV226Test(unittest.TestCase):
    def test_package_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_submit_release_package(Path(tmp) / "pkg", strict=True, zip_path=None)
            manifest = result["manifest"]
            self.assertEqual(manifest["package_id"], PACKAGE_ID)
            self.assertEqual(manifest["version"], PACKAGE_VERSION)
            self.assertEqual(result["validation"]["verification_status"], "PASS")
        print("SUBMIT_RELEASE_SCHEMA_PASS")

    def test_final_preprint_title_and_abstract(self):
        text = final_preprint_text()
        self.assertIn("# " + PREPRINT_TITLE, text)
        self.assertIn("Witnora does not claim a proof of P vs NP or a polynomial-time algorithm for SAT.", text)
        self.assertIn("TC-063 is stated as a restricted theorem with proof obligations over SAF(c,r), not as an all-SAT or hierarchy-completeness result.", text)
        self.assertIn("Native Witnora certificates are not DRAT/LRAT/FRAT proofs unless explicitly exported and externally checked.", text)
        print("FINAL_PREPRINT_TITLE_PASS")
        print("FINAL_PREPRINT_ABSTRACT_PASS")

    def test_final_preprint_limitations(self):
        text = final_preprint_text()
        for required in [
            "No P-vs-NP proof.",
            "No polynomial-time SAT algorithm.",
            "No all-SAT or hierarchy-completeness claim.",
            "TC-063 remains RESTRICTED_THEOREM_WITH_PROOF_OBLIGATIONS.",
            "G5 affine soundness is a dependency.",
            "Native certificates are not DRAT/LRAT/FRAT.",
            "Finite tests and scaling runs support implementation, not proof.",
        ]:
            self.assertIn(required, text)
        print("FINAL_PREPRINT_LIMITATIONS_PASS")


if __name__ == "__main__":
    unittest.main()
