import tempfile
import unittest
from pathlib import Path

from witnora_core.paper_hardening import (
    EXPECTED_TEST_COUNT,
    build_paper_hardening_package,
    external_review_packet_text,
    validate_paper_hardening_package,
)


class V213ExternalReviewPacketTest(unittest.TestCase):
    def test_external_review_packet_updated(self):
        packet = external_review_packet_text()
        self.assertIn("One-page summary", packet)
        self.assertIn("Expected validation status", packet)
        self.assertIn(str(EXPECTED_TEST_COUNT), packet)
        print("EXTERNAL_REVIEW_PACKET_UPDATED_PASS")

    def test_validation_script_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = build_paper_hardening_package(out_root=Path(tmp) / "pkg", zip_path="")
            validation = validate_paper_hardening_package(result["out_root"])
            self.assertEqual(validation["verification_status"], "PASS")
        self.assertTrue(Path("scripts/validate_v2_13_paper_package.py").is_file())
        print("V213_VALIDATION_SCRIPT_PASS")

    def test_no_external_acceptance_claim(self):
        packet = external_review_packet_text()
        self.assertIn("No external acceptance", packet)
        self.assertNotIn("External reviewers accepted this work", packet)
        print("NO_EXTERNAL_ACCEPTANCE_CLAIM_PASS")

    def test_no_peer_review_claim(self):
        packet = external_review_packet_text()
        self.assertIn("No external acceptance or peer review is claimed.", packet)
        self.assertNotIn("peer-reviewed and accepted", packet)
        print("NO_PEER_REVIEW_CLAIM_PASS")

    def test_package_outputs_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = build_paper_hardening_package(out_root=Path(tmp) / "pkg", zip_path="")
            root = Path(result["out_root"])
            for name in [
                "CONTRIBUTION_TABLE.md",
                "REVIEWER_OBJECTION_TABLE.md",
                "LIMITATIONS_AND_NONCLAIMS.md",
                "CLAIM_BOUNDARY_APPENDIX.md",
            ]:
                self.assertTrue((root / name).is_file())

    def test_no_acceptance_or_completeness_in_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = build_paper_hardening_package(out_root=Path(tmp) / "pkg", zip_path="")
            validation = result["validation"]
            self.assertEqual(validation["verification_status"], "PASS")
            self.assertFalse(validation["solver_logic_changed"])
            self.assertFalse(validation["proof_export_logic_changed"])
            self.assertFalse(validation["xor_logic_changed"])


if __name__ == "__main__":
    unittest.main()
