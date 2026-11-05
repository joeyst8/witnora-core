import json
import os
from pathlib import Path
import stat
import sys
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
    def _basic_release_files(self, root: Path) -> tuple[Path, Path, Path]:
        trust = root / "trust_card.md"
        report = root / "release_verification_report.json"
        manifest = root / "manifest.md"
        trust.write_text("# Trust Card\n", encoding="utf-8")
        report.write_text('{"verdict":"ARTIFACT_INTEGRITY_VERIFIED"}\n', encoding="utf-8")
        manifest.write_text("# Manifest\n", encoding="utf-8")
        return trust, report, manifest

    def test_release_trust_card_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trust, report, manifest = self._basic_release_files(root)

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

    def test_release_tag_alias(self):
        from scripts.attach_release_trust_card import main as attach_main

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trust, report, manifest = self._basic_release_files(root)
            out_tag = root / "out_tag"
            out_alias = root / "out_alias"
            code_tag = attach_main(
                [
                    "--tag",
                    "v1",
                    "--trust-card",
                    str(trust),
                    "--report",
                    str(report),
                    "--manifest",
                    str(manifest),
                    "--out-dir",
                    str(out_tag),
                ]
            )
            code_alias = attach_main(
                [
                    "--release-tag",
                    "v1",
                    "--trust-card",
                    str(trust),
                    "--report",
                    str(report),
                    "--manifest",
                    str(manifest),
                    "--out-dir",
                    str(out_alias),
                ]
            )
            self.assertEqual(code_tag, 0)
            self.assertEqual(code_alias, 0)
            tag_plan = json.loads((out_tag / "release_upload_plan.json").read_text(encoding="utf-8"))
            alias_plan = json.loads((out_alias / "release_upload_plan.json").read_text(encoding="utf-8"))
            self.assertEqual(tag_plan["release_tag"], alias_plan["release_tag"])
            self.assertEqual(tag_plan["upload_status"], alias_plan["upload_status"])
            self.assertEqual([asset["name"] for asset in tag_plan["assets"]], [asset["name"] for asset in alias_plan["assets"]])
            print("RELEASE_TAG_ALIAS_PASS")

    def test_release_trust_card_no_gh_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trust, report, manifest = self._basic_release_files(root)

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

    def _fake_gh(self, root: Path, *, view_success: bool) -> Path:
        if os.name == "nt":
            script = root / "fake_gh.py"
            log = root / "gh_calls.log"
            script.write_text(
                "import pathlib, sys\n"
                f"log = pathlib.Path({str(log)!r})\n"
                "log.write_text(log.read_text() + ' '.join(sys.argv[1:]) + '\\n' if log.exists() else ' '.join(sys.argv[1:]) + '\\n')\n"
                "args = sys.argv[1:]\n"
                "if args[:2] == ['release', 'view']:\n"
                f"    raise SystemExit({0 if view_success else 1})\n"
                "if args[:2] == ['release', 'upload']:\n"
                "    if '--clobber' in args:\n"
                "        raise SystemExit(9)\n"
                "    raise SystemExit(0)\n"
                "raise SystemExit(2)\n",
                encoding="utf-8",
            )
            wrapper = root / "fake_gh.cmd"
            wrapper.write_text(f"@echo off\n{sys.executable} \"{script}\" %*\nexit /b %ERRORLEVEL%\n", encoding="utf-8")
            return wrapper
        wrapper = root / "fake_gh"
        log = root / "gh_calls.log"
        wrapper.write_text(
            "#! /bin/sh\n"
            f"echo \"$@\" >> {str(log)!r}\n"
            "if [ \"$1 $2\" = \"release view\" ]; then\n"
            f"  exit {0 if view_success else 1}\n"
            "fi\n"
            "if [ \"$1 $2\" = \"release upload\" ]; then\n"
            "  for arg in \"$@\"; do [ \"$arg\" = \"--clobber\" ] && exit 9; done\n"
            "  exit 0\n"
            "fi\n"
            "exit 2\n",
            encoding="utf-8",
        )
        wrapper.chmod(wrapper.stat().st_mode | stat.S_IXUSR)
        return wrapper

    def test_release_tag_not_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trust, report, manifest = self._basic_release_files(root)
            fake_gh = self._fake_gh(root, view_success=False)
            plan = build_upload_plan(
                release_tag="missing-tag",
                trust_card_path=trust,
                report_path=report,
                manifest_path=manifest,
                mode="upload",
                gh_cli=str(fake_gh),
            )
            self.assertEqual(plan["upload_status"], "RELEASE_TAG_NOT_FOUND")
            self.assertIn("RELEASE_TAG_NOT_FOUND", plan["risk_flags"])
            self.assertIn("no upload attempted", " ".join(plan["messages"]))
            calls = (root / "gh_calls.log").read_text(encoding="utf-8")
            self.assertIn("release view missing-tag", calls)
            self.assertNotIn("release upload", calls)
            print("RELEASE_TAG_NOT_FOUND_PASS")

    def test_release_trust_upload_no_clobber_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trust, report, manifest = self._basic_release_files(root)
            fake_gh = self._fake_gh(root, view_success=True)
            plan = build_upload_plan(
                release_tag="v1",
                trust_card_path=trust,
                report_path=report,
                manifest_path=manifest,
                mode="upload",
                gh_cli=str(fake_gh),
            )
            self.assertEqual(plan["upload_status"], "UPLOADED")
            calls = (root / "gh_calls.log").read_text(encoding="utf-8")
            self.assertIn("release upload v1", calls)
            self.assertNotIn("--clobber", calls)
            print("RELEASE_TRUST_UPLOAD_NO_CLOBBER_DEFAULT_PASS")

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

    def test_release_automation_no_solver_logic_change(self):
        helper = Path("scripts/attach_release_trust_card.py").read_text(encoding="utf-8")
        self.assertNotIn("from witnora_core.runner", helper)
        self.assertNotIn("import witnora_core.runner", helper)
        self.assertNotIn("solve_formula", helper)
        print("RELEASE_AUTOMATION_NO_SOLVER_LOGIC_CHANGE_PASS")


if __name__ == "__main__":
    unittest.main()
