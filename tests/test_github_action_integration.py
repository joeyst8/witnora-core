import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

from witnora_core.ci import main as ci_main
from witnora_core.independent_check import verify_wcert_raw
from witnora_core.runner import main as runner_main


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


class GitHubActionIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls._tmp.name)
        cls.source_zip = cls.root / "source.zip"
        with zipfile.ZipFile(cls.source_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("README.md", "source artifact\n")

        dimacs = cls.root / "unit_unsat.dimacs"
        _write_dimacs(dimacs, [[1], [-1]], 1)
        cls.fake_checker = _fake_checker(cls.root / "fake_drat_trim", success=True)
        cert = cls.root / "unit.wcert"
        with contextlib.redirect_stdout(io.StringIO()):
            runner_main(
                [
                    str(dimacs),
                    "--c",
                    "2",
                    "--export-cert",
                    str(cert),
                    "--export-drat",
                    "--drat-trim",
                    str(cls.fake_checker),
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
                archive.writestr(log_path, "c parsing input formula\ns VERIFIED\n")
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
        cls.bad_manifest = cls.root / "bad_manifest.md"
        cls.bad_manifest.write_text(
            cls.manifest.read_text(encoding="utf-8").replace(_sha256(cls.source_zip), "0" * 64),
            encoding="utf-8",
        )

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def _ci(self, *extra: str, out_name: str = "out") -> tuple[int, dict[str, object], str]:
        out_dir = self.root / out_name
        argv = [
            "--source-zip",
            str(self.source_zip),
            "--diagnostic-zip",
            str(self.diagnostic_zip),
            "--manifest",
            str(self.manifest),
            "--out-dir",
            str(out_dir),
        ]
        argv.extend(extra)
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = ci_main(argv)
        report = json.loads((out_dir / "release_verification_report.json").read_text(encoding="utf-8"))
        return code, report, stdout.getvalue()

    def test_github_action_metadata(self):
        action = Path(".github/actions/witnora-verify/action.yml").read_text(encoding="utf-8")
        for required in [
            "source-zip:",
            "diagnostic-zip:",
            "manifest:",
            "depth:",
            "select:",
            "rerun-drat-trim:",
            "fail-on:",
            "verdict:",
            "certification_level:",
            "trust_card_path:",
            "python -m witnora_core.ci",
        ]:
            self.assertIn(required, action)
        print("GITHUB_ACTION_METADATA_PASS")

    def test_ci_wrapper_metadata_mode(self):
        code, report, output = self._ci("--depth", "metadata", out_name="metadata")
        self.assertEqual(code, 0, output)
        self.assertEqual(report["verdict"], "ARTIFACT_INTEGRITY_VERIFIED")
        self.assertEqual(report["verification_depth"], "metadata_hash_checks_only")
        print("CI_WRAPPER_METADATA_MODE_PASS")

    def test_ci_wrapper_partial_mode(self):
        code, report, output = self._ci("--depth", "partial", "--select", "largest", out_name="partial")
        self.assertEqual(code, 0, output)
        self.assertEqual(report["verdict"], "PARTIAL_REPLAY_VERIFIED_WITH_SCOPE_LIMITS")
        self.assertEqual(report["verification_depth"], "partial_replay")
        self.assertEqual(report["selected_evidence"][0]["instance_id"], "tseitin_20")
        print("CI_WRAPPER_PARTIAL_MODE_PASS")

    def test_ci_fail_on_hash_mismatch(self):
        out_dir = self.root / "bad"
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = ci_main(
                [
                    "--source-zip",
                    str(self.source_zip),
                    "--diagnostic-zip",
                    str(self.diagnostic_zip),
                    "--manifest",
                    str(self.bad_manifest),
                    "--fail-on",
                    "hash_mismatch,partial_or_not_verified",
                    "--out-dir",
                    str(out_dir),
                ]
            )
        report = json.loads((out_dir / "release_verification_report.json").read_text(encoding="utf-8"))
        self.assertNotEqual(code, 0)
        self.assertIn("HASH_MISMATCH", report["risk_flags"])
        print("CI_FAIL_ON_HASH_MISMATCH_PASS")

    def test_ci_no_fail_on_metadata_drat_not_rerun(self):
        code, report, output = self._ci("--depth", "metadata", out_name="metadata_no_drat")
        self.assertEqual(code, 0, output)
        self.assertIn("DRAT_TRIM_NOT_RERUN", report["risk_flags"])
        print("CI_NO_FAIL_ON_METADATA_DRAT_NOT_RERUN_PASS")

    def test_proof_selection_limited_flag(self):
        _code, report, _output = self._ci("--depth", "partial", "--select", "largest", out_name="limited")
        self.assertEqual(report["candidate_evidence_count"], 2)
        self.assertEqual(report["selected_evidence_count"], 1)
        self.assertIn("PROOF_SELECTION_LIMITED", report["risk_flags"])
        trust_card = (self.root / "limited" / "trust_card.md").read_text(encoding="utf-8")
        self.assertIn("Only selected proof evidence was replayed", trust_card)
        print("PROOF_SELECTION_LIMITED_FLAG_PASS")

    def test_github_output_writing(self):
        output_file = self.root / "github_output.txt"
        old_output = os.environ.get("GITHUB_OUTPUT")
        os.environ["GITHUB_OUTPUT"] = str(output_file)
        try:
            code, report, output = self._ci("--depth", "metadata", out_name="github_output")
        finally:
            if old_output is None:
                os.environ.pop("GITHUB_OUTPUT", None)
            else:
                os.environ["GITHUB_OUTPUT"] = old_output
        self.assertEqual(code, 0, output)
        lines = output_file.read_text(encoding="utf-8")
        self.assertIn(f"verdict={report['verdict']}", lines)
        self.assertIn("report_path=", lines)
        self.assertIn("trust_card_path=", lines)
        print("GITHUB_OUTPUT_WRITING_PASS")

    def test_github_action_no_solver_logic_change(self):
        combined = (
            Path("witnora_core/ci.py").read_text(encoding="utf-8")
            + Path("witnora_core/verification_report.py").read_text(encoding="utf-8")
            + Path("witnora_core/partial_replay.py").read_text(encoding="utf-8")
        )
        self.assertNotIn("from .runner", combined)
        self.assertNotIn("import witnora_core.runner", combined)
        print("GITHUB_ACTION_NO_SOLVER_LOGIC_CHANGE_PASS")


if __name__ == "__main__":
    unittest.main()
