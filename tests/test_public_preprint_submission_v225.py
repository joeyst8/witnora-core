import tempfile
import unittest
from pathlib import Path

from witnora_core.public_preprint_prep_v225 import (
    release_notes_text,
    reviewer_outreach_email_text,
    run_public_preprint_package,
    submission_checklist_text,
    validate_public_preprint_package,
)


class PublicPreprintSubmissionV225Test(unittest.TestCase):
    def test_release_notes(self):
        text = release_notes_text()
        self.assertIn("What v2.25 Is", text)
        self.assertIn("What Is Not Claimed", text)
        self.assertIn("PENDING_SOURCE_ARCHIVE_FREEZE", text)
        print("PUBLIC_PREPRINT_RELEASE_NOTES_PASS")

    def test_reviewer_email(self):
        text = reviewer_outreach_email_text()
        self.assertIn("seeking external feedback", text)
        self.assertIn("not a claim of P vs NP progress", text)
        self.assertIn("reproducibility instructions", text)
        print("PUBLIC_PREPRINT_REVIEWER_EMAIL_PASS")

    def test_submission_checklist(self):
        text = submission_checklist_text()
        self.assertIn("Title reviewed.", text)
        self.assertIn("No forbidden claims.", text)
        self.assertIn("Venue/preprint target chosen externally by user.", text)
        print("PUBLIC_PREPRINT_SUBMISSION_CHECKLIST_PASS")

    def test_package_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pkg"
            run_public_preprint_package(root, strict=True, zip_path=None)
            check = validate_public_preprint_package(root)
            self.assertEqual(check["verification_status"], "PASS")

    def test_output_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pkg"
            run_public_preprint_package(root, strict=True, zip_path=None)
            self.assertTrue((root / "PREPRINT_PREPARATION_REPORT.md").is_file())
            self.assertTrue((root / "submission_readiness_summary.json").is_file())


if __name__ == "__main__":
    unittest.main()
