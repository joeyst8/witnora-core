import tempfile
import unittest
from pathlib import Path

from witnora_core.public_preprint_prep_v225 import (
    validate_public_preprint_package,
    public_preprint_text,
    run_public_preprint_package,
)


class PublicPreprintClaimsV225Test(unittest.TestCase):
    def test_claim_scan_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pkg"
            result = run_public_preprint_package(root, strict=True, zip_path=None)
            self.assertEqual(result["validation"]["verification_status"], "PASS")
            print("PUBLIC_PREPRINT_CLAIM_SCAN_PASS")

    def test_rejects_affirmative_pnp_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pkg"
            run_public_preprint_package(root, strict=True, zip_path=None)
            paper = root / "PUBLIC_PREPRINT_DRAFT.md"
            paper.write_text(paper.read_text(encoding="utf-8") + "\n\nWe solved P vs NP.\n", encoding="utf-8")
            check = validate_public_preprint_package(root)
            self.assertEqual(check["verification_status"], "FAIL")
        print("PUBLIC_PREPRINT_NO_PNP_CLAIM_PASS")

    def test_no_all_sat_completeness_or_unqualified_theorem_claim(self):
        text = public_preprint_text()
        self.assertIn("not as an all-SAT or hierarchy-completeness result", text)
        self.assertIn("TC-063 is not theorem-proven-unqualified", text)
        self.assertNotIn("all-SAT coverage is claimed", text)
        self.assertNotIn("hierarchy completeness is claimed", text)
        print("PUBLIC_PREPRINT_NO_ALL_SAT_CLAIM_PASS")
        print("PUBLIC_PREPRINT_NO_COMPLETENESS_CLAIM_PASS")
        print("PUBLIC_PREPRINT_NO_THEOREM_PROVEN_UNQUALIFIED_PASS")

    def test_no_fake_drat_or_hard_unknown_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pkg"
            run_public_preprint_package(root, strict=True, zip_path=None)
            scan = (root / "forbidden_claim_scan.json").read_text(encoding="utf-8")
            self.assertIn('"verification_status": "PASS"', scan)
            self.assertNotIn('"HARD"', scan)
            self.assertNotIn('"UNKNOWN"', scan)
        print("PUBLIC_PREPRINT_NO_FAKE_DRAT_LRAT_FRAT_PASS")
        print("PUBLIC_PREPRINT_NO_HARD_UNKNOWN_STATUS_PASS")


if __name__ == "__main__":
    unittest.main()
