import contextlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import zipfile

from witnora_core.verification_report import (
    render_verification_report_markdown,
    sha256_file,
    trust_card_from_report,
    verification_report_for_release,
)
from witnora_core.verify import main as verify_main


def _make_zip(path: Path, name: str, content: str) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(name, content)


class VerificationKernelTest(unittest.TestCase):
    def _fixture_release(self, root: Path) -> tuple[Path, Path, Path]:
        source_zip = root / "source.zip"
        diagnostic_zip = root / "diagnostic.zip"
        _make_zip(source_zip, "README.md", "source artifact\n")
        _make_zip(diagnostic_zip, "REPORT.md", "diagnostic artifact\n")
        source_hash = sha256_file(source_zip)
        diagnostic_hash = sha256_file(diagnostic_zip)
        manifest = root / "manifest.md"
        manifest.write_text(
            "\n".join(
                [
                    "# Demo Manifest",
                    "",
                    "| asset | SHA256 | status |",
                    "| --- | --- | --- |",
                    f"| `source.zip` | `{source_hash}` | source archive |",
                    f"| `diagnostic.zip` | `{diagnostic_hash}` | diagnostic artifact |",
                    "",
                    "Validation: 188 tests passed with real drat-trim.",
                    "This release does not claim parity support, broad XOR extraction, or P vs NP progress.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return source_zip, diagnostic_zip, manifest

    def test_verification_report_schema(self):
        with TemporaryDirectory() as tmp:
            source_zip, diagnostic_zip, manifest = self._fixture_release(Path(tmp))
            report = verification_report_for_release(
                source_zip=source_zip,
                diagnostic_zip=diagnostic_zip,
                manifest=manifest,
            )
        required = {
            "claim",
            "logical_status",
            "discovery_route",
            "certification_level",
            "public_category",
            "evidence_files",
            "external_checkers",
            "checker_results",
            "artifact_hashes",
            "reproducibility_status",
            "verification_depth",
            "evidence_checked",
            "checks_performed",
            "claim_scan_depth",
            "last_verification_timestamp",
            "allowed_claims",
            "forbidden_claims",
            "risk_flags",
            "verdict",
        }
        self.assertTrue(required.issubset(report))
        self.assertEqual(report["verdict"], "ARTIFACT_INTEGRITY_VERIFIED")
        self.assertEqual(report["certification_level"], "RELEASE_ARTIFACT_INTEGRITY_VERIFIED")
        self.assertEqual(report["verification_depth"], "metadata_hash_checks_only")
        print("VERIFICATION_REPORT_SCHEMA_PASS")

    def test_release_verification_report(self):
        with TemporaryDirectory() as tmp:
            source_zip, diagnostic_zip, manifest = self._fixture_release(Path(tmp))
            out_dir = Path(tmp) / "out"
            with contextlib.redirect_stdout(io.StringIO()):
                code = verify_main(
                    [
                        "release",
                        "--source-zip",
                        str(source_zip),
                        "--diagnostic-zip",
                        str(diagnostic_zip),
                        "--manifest",
                        str(manifest),
                        "--out-dir",
                        str(out_dir),
                    ]
                )
            report = json.loads((out_dir / "release_verification_report.json").read_text(encoding="utf-8"))
            markdown_exists = (out_dir / "release_verification_report.md").exists()
        self.assertEqual(code, 0)
        self.assertEqual(report["verdict"], "ARTIFACT_INTEGRITY_VERIFIED")
        self.assertTrue(markdown_exists)
        print("RELEASE_VERIFICATION_REPORT_PASS")

    def test_trust_card_generation(self):
        with TemporaryDirectory() as tmp:
            source_zip, diagnostic_zip, manifest = self._fixture_release(Path(tmp))
            report = verification_report_for_release(
                source_zip=source_zip,
                diagnostic_zip=diagnostic_zip,
                manifest=manifest,
            )
            card = trust_card_from_report(report)
        self.assertEqual(card["project"], "Witnora-Core")
        self.assertEqual(card["verdict"], "VERIFIED_ARTIFACT_INTEGRITY_WITH_SCOPE_LIMITS")
        self.assertEqual(card["verification_depth"], "metadata_hash_checks_only")
        self.assertIn("P vs NP progress", card["not_claimed"])
        print("TRUST_CARD_GENERATION_PASS")

    def test_human_audit_report_generation(self):
        with TemporaryDirectory() as tmp:
            source_zip, diagnostic_zip, manifest = self._fixture_release(Path(tmp))
            report = verification_report_for_release(
                source_zip=source_zip,
                diagnostic_zip=diagnostic_zip,
                manifest=manifest,
            )
            markdown = render_verification_report_markdown(report)
        for heading in [
            "Claim Being Audited",
            "Evidence Provided",
            "Checks Performed",
            "Evidence Checked",
            "Verification Depth",
            "External Verification",
            "Artifact Hashes",
            "Certification Level",
            "Allowed Claims",
            "Forbidden Claims",
            "Risk Flags",
            "Claim Boundary Scanner Limitation",
            "Final Verdict",
        ]:
            self.assertIn(heading, markdown)
        self.assertIn("metadata and artifact-integrity check", markdown)
        print("HUMAN_AUDIT_REPORT_GENERATION_PASS")

    def test_no_solver_logic_change_marker(self):
        verify_source = Path("witnora_core/verify.py").read_text(encoding="utf-8")
        report_source = Path("witnora_core/verification_report.py").read_text(encoding="utf-8")
        combined = verify_source + report_source
        self.assertNotIn("from .runner", combined)
        self.assertNotIn("import witnora_core.runner", combined)
        self.assertNotIn("solve(", combined)
        print("VERIFICATION_KERNEL_NO_SOLVER_LOGIC_CHANGE_PASS")


if __name__ == "__main__":
    unittest.main()
