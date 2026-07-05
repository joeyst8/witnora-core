import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.attach_release_trust_card import build_upload_plan, write_upload_plan
from witnora_core.verification_report import sha256_file, verification_report_for_release


def _write_zip(path: Path, entries: dict[str, str]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, text in entries.items():
            archive.writestr(name, text)


def _manifest(path: Path, source: Path, diagnostic: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# Manifest",
                "",
                "| asset | SHA256 | status |",
                "| --- | --- | --- |",
                f"| `{source.name}` | `{sha256_file(source)}` | source archive |",
                f"| `{diagnostic.name}` | `{sha256_file(diagnostic)}` | diagnostic artifact |",
                "",
                "This release does not claim parity support, broad XOR extraction, or P vs NP progress.",
                "",
            ]
        ),
        encoding="utf-8",
    )


class ReleaseTrustCardAutomationTest(unittest.TestCase):
    def test_release_trust_card_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trust = root / "trust_card.md"
            report = root / "release_verification_report.json"
            manifest = root / "manifest.md"
            trust.write_text("# Trust Card\n", encoding="utf-8")
            report.write_text('{"verdict":"ARTIFACT_INTEGRITY_VERIFIED"}\n', encoding="utf-8")
            manifest.write_text("# Manifest\n", encoding="utf-8")

            plan = build_upload_plan(
                release_tag="v1",
                trust_card_path=trust,
                report_path=report,
                manifest_path=manifest,
            )
            json_path, md_path, snippet_path = write_upload_plan(plan, root / "out")

            self.assertEqual(plan["upload_status"], "DRY_RUN")
            self.assertTrue(json_path.is_file())
            self.assertTrue(md_path.is_file())
            self.assertTrue(snippet_path.is_file())
            self.assertIn("trust_card.md", md_path.read_text(encoding="utf-8"))
            print("RELEASE_TRUST_CARD_DRY_RUN_PASS")

    def test_release_trust_card_no_gh_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trust = root / "trust_card.md"
            report = root / "release_verification_report.json"
            manifest = root / "manifest.md"
            trust.write_text("# Trust Card\n", encoding="utf-8")
            report.write_text('{"verdict":"ARTIFACT_INTEGRITY_VERIFIED"}\n', encoding="utf-8")
            manifest.write_text("# Manifest\n", encoding="utf-8")

            plan = build_upload_plan(
                release_tag="v1",
                trust_card_path=trust,
                report_path=report,
                manifest_path=manifest,
                mode="upload",
                gh_cli="definitely-not-gh-witnora",
            )
            self.assertEqual(plan["upload_status"], "GITHUB_CLI_NOT_AVAILABLE")
            self.assertIn("gh CLI was not available", " ".join(plan["messages"]))
            print("RELEASE_TRUST_CARD_NO_GH_CLI_PASS")

    def test_proof_file_missing_risk_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.zip"
            diagnostic = root / "diagnostic.zip"
            manifest = root / "manifest.md"
            _write_zip(source, {"README.md": "source\n"})
            artifact_root = "outputs/v0.9.8-full-tseitin-minfill-diagnostic"
            cert_prefix = f"{artifact_root}/certs/default/sparse-min-fill/c2/tseitin_missing.wcert"
            proof_path = f"{cert_prefix}/proof.drat"
            row = {
                "instance_id": "tseitin_missing",
                "family": "tseitin",
                "c": 2,
                "cap_profile": "default",
                "public_category": "UNSAT_DRAT_EXPORTED_VERIFIED",
                "certificate_path": cert_prefix,
                "proof_drat_path": proof_path,
                "drat_trim_log_path": f"{artifact_root}/drat_logs/missing.log",
                "external_checker_verified": True,
                "original_num_vars": 20,
                "original_num_clauses": 80,
            }
            _write_zip(
                diagnostic,
                {
                    f"{artifact_root}/manifest.json": "{}\n",
                    f"{artifact_root}/FULL_TSEITIN_MINFILL_DIAGNOSTIC_REPORT.md": "# Report\n",
                    f"{artifact_root}/per_instance_results.json": json.dumps({"rows": [row]}),
                    f"{cert_prefix}/original.dimacs": "p cnf 1 1\n1 0\n",
                    f"{artifact_root}/drat_logs/missing.log": "s VERIFIED\n",
                    f"{artifact_root}/independent_checks/missing.json": "{}\n",
                },
            )
            _manifest(manifest, source, diagnostic)

            report = verification_report_for_release(
                source_zip=source,
                diagnostic_zip=diagnostic,
                manifest=manifest,
                depth="partial",
                selection_policy="largest",
            )
            self.assertIn("PROOF_FILE_MISSING", report["risk_flags"])
            self.assertEqual(report["verdict"], "PARTIALLY_VERIFIED")
            self.assertNotEqual(report["verdict"], "PARTIAL_REPLAY_VERIFIED_WITH_SCOPE_LIMITS")
            print("PROOF_FILE_MISSING_RISK_FLAG_PASS")


if __name__ == "__main__":
    unittest.main()
