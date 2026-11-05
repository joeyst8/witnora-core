import json
import tempfile
import unittest
from pathlib import Path

from witnora_core.external_review_package_v224 import (
    PACKAGE_ID,
    PACKAGE_VERSION,
    REQUIRED_JSON,
    REQUIRED_MARKDOWN,
    check_external_review_package,
    run_external_review_package,
)


class ExternalReviewPackageV224Test(unittest.TestCase):
    def test_package_schema_and_required_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pkg"
            result = run_external_review_package(root, strict=True, zip_path=None)
            manifest = json.loads((root / "external_review_package_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["package_id"], PACKAGE_ID)
            self.assertEqual(manifest["version"], PACKAGE_VERSION)
            self.assertEqual(result["validation"]["verification_status"], "PASS")
            for name in REQUIRED_MARKDOWN:
                self.assertTrue((root / name).is_file(), name)
            for name in REQUIRED_JSON:
                self.assertTrue((root / name).is_file(), name)
            print("EXTERNAL_REVIEW_PACKAGE_SCHEMA_PASS")
            print("EXTERNAL_REVIEW_PACKAGE_COMPLETE_PASS")

    def test_package_checker_rejects_forbidden_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pkg"
            run_external_review_package(root, strict=True, zip_path=None)
            paper = root / "WITNORA_COLLAPSE_HIERARCHY_EXTERNAL_REVIEW_DRAFT.md"
            paper.write_text(paper.read_text(encoding="utf-8") + "\n\nWe solved P vs NP.\n", encoding="utf-8")
            check = check_external_review_package(root)
            self.assertEqual(check["verification_status"], "FAIL")
            self.assertTrue(any(error.startswith("FORBIDDEN_CLAIM") for error in check["errors"]))

    def test_tc063_and_g9_g13_appendices(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pkg"
            run_external_review_package(root, strict=True, zip_path=None)
            tc063 = (root / "TC063_THEOREM_APPENDIX.md").read_text(encoding="utf-8")
            g9_g13 = (root / "G9_G13_SOUNDNESS_APPENDIX.md").read_text(encoding="utf-8")
            obligations = json.loads((root / "tc063_obligation_manifest.json").read_text(encoding="utf-8"))
            self.assertIn("SAF(c,r)", tc063)
            self.assertIn("TC-063 status: RESTRICTED_THEOREM_WITH_PROOF_OBLIGATIONS", tc063)
            self.assertIn("TC-063 is not THEOREM_PROVEN_UNQUALIFIED", tc063)
            self.assertEqual(len(obligations["lemmas"]), 8)
            self.assertEqual(len(obligations["proof_obligations"]), 32)
            for grammar in ["G9", "G10", "G11", "G12", "G13"]:
                self.assertIn(grammar, g9_g13)
            print("EXTERNAL_REVIEW_TC063_APPENDIX_PASS")
            print("EXTERNAL_REVIEW_G9_G13_APPENDIX_PASS")


if __name__ == "__main__":
    unittest.main()
