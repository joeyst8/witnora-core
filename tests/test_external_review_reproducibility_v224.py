import tempfile
import unittest
from pathlib import Path

from witnora_core.external_review_package_v224 import (
    reproducibility_guide_text,
    reviewer_guide_text,
    run_external_review_package,
)


class ExternalReviewReproducibilityV224Test(unittest.TestCase):
    def test_reviewer_guide(self):
        text = reviewer_guide_text()
        for required in [
            "What to Inspect First",
            "How to Reproduce Tests",
            "How to Attack the Framework",
            "Known Limitations",
        ]:
            self.assertIn(required, text)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pkg"
            run_external_review_package(root, strict=True, zip_path=None)
            self.assertTrue(Path("docs/REVIEWER_GUIDE.md").is_file())
            self.assertTrue((root / "REVIEWER_GUIDE_V2_24.md").is_file())
        print("EXTERNAL_REVIEW_REVIEWER_GUIDE_PASS")

    def test_reproducibility_guide(self):
        text = reproducibility_guide_text()
        for required in [
            "Environment Assumptions",
            "Set WITNORA_DRAT_TRIM",
            "Run Full Tests",
            "Regenerate v2.24 Package",
            "Verify SHA256",
        ]:
            self.assertIn(required, text)
        print("EXTERNAL_REVIEW_REPRODUCIBILITY_GUIDE_PASS")


if __name__ == "__main__":
    unittest.main()
