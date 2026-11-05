import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import zipfile

from witnora_core.verification_report import (
    CLAIM_SCANNER_LIMITATION_TEXT,
    render_verification_report_markdown,
    render_trust_card_markdown,
    sha256_file,
    trust_card_from_report,
    verification_report_for_release,
)


def _make_zip(path: Path, name: str, content: str) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(name, content)


def _fixture_release(root: Path) -> tuple[Path, Path, Path]:
    source_zip = root / "source.zip"
    diagnostic_zip = root / "diagnostic.zip"
    _make_zip(source_zip, "README.md", "source artifact\n")
    _make_zip(diagnostic_zip, "REPORT.md", "diagnostic artifact\n")
    manifest = root / "manifest.md"
    manifest.write_text(
        "\n".join(
            [
                "# Demo Manifest",
                "",
                "| asset | SHA256 | status |",
                "| --- | --- | --- |",
                f"| `source.zip` | `{sha256_file(source_zip)}` | source archive |",
                f"| `diagnostic.zip` | `{sha256_file(diagnostic_zip)}` | diagnostic artifact |",
                "",
                "Validation: 188 tests passed with real drat-trim.",
                "This release does not claim parity support, broad XOR extraction, competitive SAT solving, or P vs NP progress.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return source_zip, diagnostic_zip, manifest


class VerificationSemanticsTest(unittest.TestCase):
    def _report(self) -> dict[str, object]:
        with TemporaryDirectory() as tmp:
            source_zip, diagnostic_zip, manifest = _fixture_release(Path(tmp))
            return verification_report_for_release(
                source_zip=source_zip,
                diagnostic_zip=diagnostic_zip,
                manifest=manifest,
            )

    def test_no_broad_verified_release_verdict(self):
        report = self._report()
        self.assertNotEqual(report["verdict"], "VERIFIED")
        self.assertNotEqual(report["certification_level"], "RELEASE_EVIDENCE_VERIFIED")
        print("VERIFICATION_SEMANTICS_NO_BROAD_VERIFIED_PASS")

    def test_artifact_integrity_verdict(self):
        report = self._report()
        self.assertEqual(report["verdict"], "ARTIFACT_INTEGRITY_VERIFIED")
        self.assertEqual(report["certification_level"], "RELEASE_ARTIFACT_INTEGRITY_VERIFIED")
        print("ARTIFACT_INTEGRITY_VERDICT_PASS")

    def test_trust_card_scoped_verdict(self):
        card = trust_card_from_report(self._report())
        self.assertEqual(card["verdict"], "VERIFIED_ARTIFACT_INTEGRITY_WITH_SCOPE_LIMITS")
        print("TRUST_CARD_SCOPED_VERDICT_PASS")

    def test_verification_depth_metadata_only(self):
        report = self._report()
        card = trust_card_from_report(report)
        self.assertEqual(report["verification_depth"], "metadata_hash_checks_only")
        self.assertEqual(card["verification_depth"], "metadata_hash_checks_only")
        print("VERIFICATION_DEPTH_METADATA_ONLY_PASS")

    def test_metadata_only_risk_flags(self):
        report = self._report()
        for flag in [
            "METADATA_ONLY",
            "DRAT_TRIM_NOT_RERUN",
            "INDEPENDENT_CHECKER_NOT_RERUN",
            "CLAIM_SCAN_HEURISTIC_ONLY",
        ]:
            self.assertIn(flag, report["risk_flags"])
        print("METADATA_ONLY_RISK_FLAGS_PASS")

    def test_evidence_checked_fields(self):
        report = self._report()
        self.assertIn("evidence_checked", report)
        self.assertIn("checks_performed", report)
        self.assertIn("last_verification_timestamp", report)
        self.assertGreaterEqual(len(report["evidence_checked"]), 3)
        self.assertGreaterEqual(len(report["checks_performed"]), 3)
        self.assertTrue(str(report["last_verification_timestamp"]).endswith("Z"))
        for item in report["evidence_checked"]:
            for key in ["path", "kind", "sha256_expected", "sha256_actual", "status"]:
                self.assertIn(key, item)
        print("EVIDENCE_CHECKED_FIELDS_PASS")

    def test_claim_scanner_limitation_doc(self):
        report_markdown = render_verification_report_markdown(self._report())
        self.assertIn(CLAIM_SCANNER_LIMITATION_TEXT, report_markdown)
        self.assertIn("claim_scan_depth: `heuristic_text_scan`", report_markdown)
        print("CLAIM_SCANNER_LIMITATION_DOC_PASS")

    def test_vision_doc_forward_looking_disclaimer(self):
        vision = Path("docs/VERIFIABLE_INTELLIGENCE_VISION.md").read_text(encoding="utf-8")
        product = Path("docs/PRODUCT_WEDGE.md").read_text(encoding="utf-8")
        disclaimer = (
            "This is a forward-looking vision document. It does not describe "
            "current production capabilities."
        )
        self.assertIn(disclaimer, vision)
        self.assertIn(disclaimer, product)
        print("VISION_DOC_FORWARD_LOOKING_DISCLAIMER_PASS")

    def test_trust_card_markdown_scope_statement(self):
        card_markdown = render_trust_card_markdown(trust_card_from_report(self._report()))
        self.assertIn("artifact integrity and scope boundaries only", card_markdown)
        self.assertIn("does not rerun the scientific proof pipeline", card_markdown)


if __name__ == "__main__":
    unittest.main()
