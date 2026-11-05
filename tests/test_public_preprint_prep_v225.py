import tempfile
import unittest
from pathlib import Path

from witnora_core.public_preprint_prep_v225 import (
    PACKAGE_ID,
    PACKAGE_VERSION,
    PREPRINT_TITLE,
    public_preprint_text,
    run_public_preprint_package,
)


class PublicPreprintPrepV225Test(unittest.TestCase):
    def test_package_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_public_preprint_package(Path(tmp) / "pkg", strict=True, zip_path=None)
            manifest = result["manifest"]
            self.assertEqual(manifest["package_id"], PACKAGE_ID)
            self.assertEqual(manifest["version"], PACKAGE_VERSION)
            self.assertEqual(result["validation"]["verification_status"], "PASS")
        print("PUBLIC_PREPRINT_PREP_SCHEMA_PASS")

    def test_title(self):
        text = public_preprint_text()
        self.assertIn("# " + PREPRINT_TITLE, text)
        self.assertNotIn("Solving P vs NP", text)
        self.assertNotIn("Polynomial-Time SAT", text)
        print("PUBLIC_PREPRINT_TITLE_PASS")

    def test_abstract_nonclaims(self):
        text = public_preprint_text()
        self.assertIn("Witnora does not claim a proof of P vs NP or a polynomial-time algorithm for SAT.", text)
        self.assertIn("TC-063 is stated as a restricted theorem with proof obligations over SAF(c,r), not as an all-SAT or hierarchy-completeness result.", text)
        self.assertIn("Native Witnora certificates are not DRAT/LRAT/FRAT proofs unless explicitly exported and externally checked.", text)
        print("PUBLIC_PREPRINT_ABSTRACT_NONCLAIMS_PASS")

    def test_contributions(self):
        text = public_preprint_text()
        for contribution in [
            "Collapse hierarchy G0-G14",
            "Native certificate framework",
            "Obstruction-to-operator loop",
            "Certified composition and planner-guided execution",
            "G9-G13 soundness backbone",
            "TC-063 restricted theorem with proof obligations",
            "Reproducible release/evidence manifests",
        ]:
            self.assertIn(contribution, text)
        print("PUBLIC_PREPRINT_CONTRIBUTIONS_PASS")


if __name__ == "__main__":
    unittest.main()
