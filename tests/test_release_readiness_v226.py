import tempfile
import unittest
from pathlib import Path

from witnora_core.submit_release_finalize_v226 import (
    arxiv_checklist_text,
    github_release_checklist_text,
    release_notes_v226_text,
    reviewer_outreach_email_text,
    run_submit_release_package,
    workshop_checklist_text,
)


class ReleaseReadinessV226Test(unittest.TestCase):
    def test_release_notes(self):
        text = release_notes_v226_text()
        self.assertIn("Citation Hardening", text)
        self.assertIn("arXiv-ready after user approval", text)
        print("RELEASE_NOTES_V226_PASS")

    def test_reviewer_email(self):
        text = reviewer_outreach_email_text()
        self.assertIn("seeking external feedback", text)
        self.assertIn("not a claim of P vs NP progress", text)
        print("REVIEWER_EMAIL_V226_PASS")

    def test_checklists(self):
        self.assertIn("Final public preprint draft generated.", arxiv_checklist_text())
        self.assertIn("Choose workshop or venue externally.", workshop_checklist_text())
        self.assertIn("Create source release archive after tag.", github_release_checklist_text())
        print("ARXIV_CHECKLIST_PASS")
        print("WORKSHOP_CHECKLIST_PASS")
        print("GITHUB_RELEASE_CHECKLIST_PASS")

    def test_package_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pkg"
            result = run_submit_release_package(root, strict=True, zip_path=None)
            self.assertEqual(result["validation"]["verification_status"], "PASS")
            for name in [
                "ARXIV_SUBMISSION_CHECKLIST.md",
                "WORKSHOP_SUBMISSION_CHECKLIST.md",
                "GITHUB_RELEASE_CHECKLIST.md",
                "BIBLIOGRAPHY_COMPLETION_REPORT.md",
            ]:
                self.assertTrue((root / name).is_file())


if __name__ == "__main__":
    unittest.main()
