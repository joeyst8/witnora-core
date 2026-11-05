import contextlib
import io
import json
import os
import sys
from pathlib import Path
import tempfile
import unittest
import zipfile

from witnora_core.independent_check import verify_wcert_raw
from witnora_core.runner import main as runner_main
from witnora_core.verification_report import (
    render_trust_card_markdown,
    trust_card_from_report,
    verification_report_for_release,
)
from witnora_core.verify import main as verify_main


def _write_dimacs(path: Path, clauses: list[list[int]], num_vars: int) -> None:
    lines = [f"p cnf {num_vars} {len(clauses)}"]
    lines.extend(" ".join(str(lit) for lit in clause) + " 0" for clause in clauses)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _fake_checker(path: Path, *, success: bool = True) -> Path:
    if os.name == "nt":
        checker = path.with_suffix(".cmd")
        checker.write_text(
            "@echo off\n"
            + ("echo s VERIFIED\nexit /b 0\n" if success else "echo s FAILED 1>&2\nexit /b 7\n"),
            encoding="utf-8",
        )
        return checker
    script = path.with_suffix(".py")
    script.write_text(
        "import sys\n"
        f"print({'s VERIFIED' if success else 's FAILED'!r}, file=sys.{'stdout' if success else 'stderr'})\n"
        f"raise SystemExit({0 if success else 7})\n",
        encoding="utf-8",
    )
    wrapper = path.with_suffix(".sh")
    wrapper.write_text(f"#! /bin/sh\nexec {sys.executable!r} {str(script)!r} \"$@\"\n", encoding="utf-8")
    wrapper.chmod(0o755)
    return wrapper


def _sha256(path: Path) -> str:
    from hashlib import sha256

    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _zip_directory(archive: zipfile.ZipFile, source: Path, destination_prefix: str) -> None:
    for file_path in source.rglob("*"):
        if file_path.is_file():
            archive.write(file_path, f"{destination_prefix}/{file_path.relative_to(source).as_posix()}")


class PartialReplayKernelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls._tmp.name)
        cls.source_zip = cls.root / "source.zip"
        with zipfile.ZipFile(cls.source_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("README.md", "source artifact\n")

        dimacs = cls.root / "unit_unsat.dimacs"
        _write_dimacs(dimacs, [[1], [-1]], 1)
        checker = _fake_checker(cls.root / "fake_drat_trim", success=True)
        cls.fake_checker = checker
        cert = cls.root / "unit.wcert"
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            runner_main(
                [
                    str(dimacs),
                    "--c",
                    "2",
                    "--export-cert",
                    str(cert),
                    "--export-drat",
                    "--drat-trim",
                    str(checker),
                ]
            )
        independent = verify_wcert_raw(cert)
        assert independent["verified"], independent

        cls.diagnostic_zip = cls.root / "diagnostic.zip"
        artifact_root = "outputs/v0.9.8-full-tseitin-minfill-diagnostic"
        rows = []
        with zipfile.ZipFile(cls.diagnostic_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(f"{artifact_root}/manifest.json", json.dumps({"suite": "fixture"}))
            archive.writestr(f"{artifact_root}/FULL_TSEITIN_MINFILL_DIAGNOSTIC_REPORT.md", "# Fixture Report\n")
            for instance, vars_count in [("tseitin_10", 20), ("tseitin_20", 40)]:
                cert_prefix = f"{artifact_root}/certs/default/sparse-min-fill/c2/{instance}.wcert"
                proof_path = f"{cert_prefix}/proof.drat"
                log_path = f"{artifact_root}/drat_logs/default_sparse-min-fill_c2_{instance}.log"
                independent_path = f"{artifact_root}/independent_checks/default_sparse-min-fill_c2_{instance}.json"
                _zip_directory(archive, cert, cert_prefix)
                archive.writestr(
                    log_path,
                    "c parsing input formula\ns VERIFIED\nc verification time: 0.001 seconds\n",
                )
                archive.writestr(independent_path, json.dumps(independent, indent=2, sort_keys=True))
                rows.append(
                    {
                        "instance_id": instance,
                        "family": "tseitin",
                        "c": 2,
                        "cap_profile": "default",
                        "public_category": "UNSAT_DRAT_EXPORTED_VERIFIED",
                        "certificate_path": cert_prefix,
                        "proof_drat_path": proof_path,
                        "drat_trim_log_path": log_path,
                        "independent_checker_path": independent_path,
                        "external_checker_verified": True,
                        "original_num_vars": vars_count,
                        "original_num_clauses": vars_count * 4,
                    }
                )
            archive.writestr(
                f"{artifact_root}/per_instance_results.json",
                json.dumps({"rows": rows}, indent=2, sort_keys=True),
            )

        cls.manifest = cls.root / "manifest.md"
        cls.manifest.write_text(
            "\n".join(
                [
                    "# Fixture Manifest",
                    "",
                    "| asset | SHA256 | status |",
                    "| --- | --- | --- |",
                    f"| `source.zip` | `{_sha256(cls.source_zip)}` | source archive |",
                    f"| `diagnostic.zip` | `{_sha256(cls.diagnostic_zip)}` | diagnostic artifact |",
                    "",
                    "This release does not claim parity support, broad XOR extraction, or P vs NP progress.",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def partial_report(self, **kwargs):
        return verification_report_for_release(
            source_zip=self.source_zip,
            diagnostic_zip=self.diagnostic_zip,
            manifest=self.manifest,
            depth="partial",
            **kwargs,
        )

    def test_partial_replay_depth_mode(self):
        report = self.partial_report()
        self.assertEqual(report["verification_depth"], "partial_replay")
        self.assertEqual(report["verdict"], "PARTIAL_REPLAY_VERIFIED_WITH_SCOPE_LIMITS")
        print("PARTIAL_REPLAY_DEPTH_MODE_PASS")

    def test_partial_replay_structure_check(self):
        report = self.partial_report()
        structure = [check for check in report["checks_performed"] if str(check["name"]).startswith("diagnostic_structure")]
        self.assertTrue(structure)
        self.assertTrue(all(check["status"] == "PASS" for check in structure))
        print("PARTIAL_REPLAY_STRUCTURE_CHECK_PASS")

    def test_partial_replay_proof_syntax_check(self):
        report = self.partial_report()
        self.assertEqual(report["proof_syntax_checks"][0]["status"], "PASS")
        self.assertTrue(report["proof_syntax_checks"][0]["has_final_empty_clause"])
        print("PARTIAL_REPLAY_PROOF_SYNTAX_CHECK_PASS")

    def test_partial_replay_drat_log_check(self):
        report = self.partial_report()
        self.assertEqual(report["drat_trim_log_checks"][0]["status"], "PASS")
        self.assertIn("s VERIFIED", report["drat_trim_log_checks"][0]["stdout_excerpt"])
        print("PARTIAL_REPLAY_DRAT_LOG_CHECK_PASS")

    def test_partial_replay_selection_largest(self):
        report = self.partial_report(selection_policy="largest")
        self.assertEqual(report["selection_policy"], "largest")
        self.assertEqual(report["selected_evidence"][0]["instance_id"], "tseitin_20")
        print("PARTIAL_REPLAY_SELECTION_LARGEST_PASS")

    def test_partial_replay_trust_card(self):
        card = trust_card_from_report(self.partial_report())
        markdown = render_trust_card_markdown(card)
        self.assertEqual(card["verdict"], "PARTIAL_REPLAY_VERIFIED_WITH_SCOPE_LIMITS")
        self.assertEqual(card["verification_depth"], "partial_replay")
        self.assertIn("partial replay of selected evidence", markdown)
        print("PARTIAL_REPLAY_TRUST_CARD_PASS")

    def test_full_replay_not_implemented(self):
        report = verification_report_for_release(
            source_zip=self.source_zip,
            diagnostic_zip=self.diagnostic_zip,
            manifest=self.manifest,
            depth="full",
        )
        self.assertEqual(report["verdict"], "NOT_VERIFIED")
        self.assertIn("FULL_REPLAY_NOT_IMPLEMENTED", report["risk_flags"])
        print("FULL_REPLAY_NOT_IMPLEMENTED_PASS")

    def test_partial_replay_no_solver_rerun(self):
        combined = (
            Path("witnora_core/verify.py").read_text(encoding="utf-8")
            + Path("witnora_core/verification_report.py").read_text(encoding="utf-8")
            + Path("witnora_core/partial_replay.py").read_text(encoding="utf-8")
        )
        self.assertNotIn("from .runner", combined)
        self.assertNotIn("import witnora_core.runner", combined)
        print("PARTIAL_REPLAY_NO_SOLVER_RERUN_PASS")

    def test_partial_replay_no_false_full_verification_claim(self):
        report = self.partial_report()
        self.assertNotEqual(report["verification_depth"], "full")
        self.assertNotIn("FULL_REPLAY_VERIFIED", json.dumps(report))
        print("PARTIAL_REPLAY_NO_FALSE_FULL_VERIFICATION_CLAIM_PASS")

    def test_partial_replay_independent_checker(self):
        report = self.partial_report()
        self.assertEqual(report["independent_checker_replay"][0]["status"], "PASS")
        self.assertEqual(report["certification_level"], "PARTIAL_REPLAY_INDEPENDENT_CHECKER_VERIFIED")
        self.assertIn("INDEPENDENT_CHECKER_RERUN", report["risk_flags"])
        print("PARTIAL_REPLAY_INDEPENDENT_CHECKER_PASS")

    def test_partial_replay_drat_trim_rerun(self):
        report = self.partial_report(rerun_drat_trim=True, drat_trim_path=self.fake_checker)
        self.assertEqual(report["drat_trim_replay"][0]["status"], "PASS")
        self.assertEqual(report["certification_level"], "PARTIAL_REPLAY_DRAT_TRIM_VERIFIED")
        self.assertIn("DRAT_TRIM_RERUN", report["risk_flags"])
        print("PARTIAL_REPLAY_DRAT_TRIM_RERUN_PASS")

    def test_partial_replay_cli(self):
        out_dir = self.root / "cli_out"
        with contextlib.redirect_stdout(io.StringIO()):
            code = verify_main(
                [
                    "release",
                    "--source-zip",
                    str(self.source_zip),
                    "--diagnostic-zip",
                    str(self.diagnostic_zip),
                    "--manifest",
                    str(self.manifest),
                    "--depth",
                    "partial",
                    "--out-dir",
                    str(out_dir),
                ]
            )
        self.assertEqual(code, 0)
        report = json.loads((out_dir / "release_verification_report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["verification_depth"], "partial_replay")


if __name__ == "__main__":
    unittest.main()
