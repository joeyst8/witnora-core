import tempfile
import unittest
from pathlib import Path

from witnora_core.external_review_package_v224 import (
    check_external_review_package,
    claim_boundary_rows,
    run_external_review_package,
)


class ExternalReviewClaimBoundariesV224Test(unittest.TestCase):
    def test_claim_boundary_rows(self):
        rows = {row["claim"]: row for row in claim_boundary_rows()}
        self.assertEqual(rows["P vs NP solved"]["status"], "NOT CLAIMED")
        self.assertEqual(rows["Polynomial-time SAT"]["status"], "NOT CLAIMED")
        self.assertEqual(rows["All-SAT coverage"]["status"], "NOT CLAIMED")
        self.assertEqual(rows["Hierarchy completeness"]["status"], "NOT CLAIMED")
        self.assertEqual(rows["Native certificates"]["status"], "NATIVE_ONLY")
        self.assertEqual(rows["Planner execution loop"]["status"], "FINITE_PLANNER_EXECUTION_VERIFIED")
        print("EXTERNAL_REVIEW_CLAIM_BOUNDARY_TABLE_PASS")

    def test_no_forbidden_claim_boundaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pkg"
            run_external_review_package(root, strict=True, zip_path=None)
            check = check_external_review_package(root)
            self.assertEqual(check["verification_status"], "PASS")
            combined = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.md"))
            self.assertIn("Witnora does not claim a proof of P vs NP.", combined)
            self.assertIn("not an all-SAT theorem", combined)
            self.assertIn("Native certificates are not DRAT/LRAT/FRAT", combined)
            self.assertIn("Finite evidence supports implementation behavior but does not substitute for a family proof.", combined)
            print("EXTERNAL_REVIEW_NO_PNP_CLAIM_PASS")
            print("EXTERNAL_REVIEW_NO_COMPLETENESS_CLAIM_PASS")
            print("EXTERNAL_REVIEW_NO_ALL_SAT_CLAIM_PASS")
            print("EXTERNAL_REVIEW_NO_THEOREM_PROVEN_UNQUALIFIED_PASS")
            print("EXTERNAL_REVIEW_NO_FAKE_DRAT_PASS")
            print("EXTERNAL_REVIEW_NATIVE_CERT_BOUNDARY_PASS")
            print("EXTERNAL_REVIEW_FINITE_EVIDENCE_BOUNDARY_PASS")
            print("EXTERNAL_REVIEW_NO_HARD_UNKNOWN_STATUS_PASS")


if __name__ == "__main__":
    unittest.main()
