import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from witnora_core.independent_check import verify_wcert_raw
from witnora_core.runner import main as runner_main


def write_dimacs(path, clauses, num_vars):
    lines = [f"p cnf {num_vars} {len(clauses)}"]
    for clause in clauses:
        lines.append(" ".join(str(lit) for lit in clause) + " 0")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_cert(dimacs_path, cert_path, drat_trim_path=None):
    args = [
        str(dimacs_path),
        "--c",
        "2",
        "--export-cert",
        str(cert_path),
        "--export-drat",
    ]
    if drat_trim_path is not None:
        args.extend(["--drat-trim", str(drat_trim_path)])
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        code = runner_main(args)
    return code, json.loads(stdout.getvalue())


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fake_checker(path, *, success):
    if os.name == "nt":
        path = path.with_suffix(".cmd")
        if success:
            text = "@echo off\necho s VERIFIED\nexit /b 0\n"
        else:
            text = "@echo off\necho s FAILED 1>&2\nexit /b 7\n"
        path.write_text(text, encoding="utf-8")
        return path
    path = path.with_suffix(".py")
    code = 0 if success else 7
    stream = "stdout" if success else "stderr"
    message = "s VERIFIED" if success else "s FAILED"
    path.write_text(
        "import sys\n"
        f"print({message!r}, file=sys.{stream})\n"
        f"raise SystemExit({code})\n",
        encoding="utf-8",
    )
    wrapper = path.with_suffix(".sh")
    wrapper.write_text(f"#! /bin/sh\nexec {sys.executable!r} {str(path)!r} \"$@\"\n", encoding="utf-8")
    wrapper.chmod(0o755)
    return wrapper


class DRATTrimIntegrationTest(unittest.TestCase):
    def test_drat_trim_not_run_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dimacs = root / "unit_unsat.dimacs"
            write_dimacs(dimacs, [[1], [-1]], 1)
            cert = root / "unit.wcert"
            code, result = export_cert(dimacs, cert)
            status = read_json(cert / "drat_status.json")
            checked = verify_wcert_raw(cert)
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "UNSAT")
        self.assertEqual(status["external_checker"], "NOT_RUN")
        self.assertFalse(status["external_checker_ran"])
        self.assertFalse(status["external_checker_verified"])
        self.assertFalse(checked["checks"]["external_drat_verified"])
        print("DRAT_TRIM_NOT_RUN_STATUS_PASS")

    def test_drat_trim_fake_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dimacs = root / "unit_unsat.dimacs"
            write_dimacs(dimacs, [[1], [-1]], 1)
            checker = fake_checker(root / "fake_success", success=True)
            cert = root / "unit.wcert"
            code, result = export_cert(dimacs, cert, checker)
            status = read_json(cert / "drat_status.json")
            checked = verify_wcert_raw(cert)
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "UNSAT")
        self.assertEqual(status["external_checker"], "DRAT_TRIM")
        self.assertTrue(status["external_checker_ran"])
        self.assertTrue(status["external_checker_verified"])
        self.assertEqual(status["external_checker_exit_code"], 0)
        self.assertIn("s VERIFIED", status["external_checker_stdout_excerpt"])
        self.assertTrue(checked["checks"]["external_drat_verified"])
        print("DRAT_TRIM_FAKE_SUCCESS_PASS")

    def test_drat_trim_fake_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dimacs = root / "unit_unsat.dimacs"
            write_dimacs(dimacs, [[1], [-1]], 1)
            checker = fake_checker(root / "fake_failure", success=False)
            cert = root / "unit.wcert"
            code, result = export_cert(dimacs, cert, checker)
            status = read_json(cert / "drat_status.json")
            checked = verify_wcert_raw(cert)
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "UNSAT")
        self.assertEqual(status["external_checker"], "DRAT_TRIM")
        self.assertTrue(status["external_checker_ran"])
        self.assertFalse(status["external_checker_verified"])
        self.assertEqual(status["external_checker_exit_code"], 7)
        self.assertIn("s FAILED", status["external_checker_stderr_excerpt"])
        self.assertFalse(checked["checks"]["external_drat_verified"])
        print("DRAT_TRIM_FAKE_FAILURE_PASS")

    def test_drat_trim_claim_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dimacs = root / "unit_unsat.dimacs"
            write_dimacs(dimacs, [[1], [-1]], 1)
            cert = root / "unit.wcert"
            export_cert(dimacs, cert)
            status = read_json(cert / "drat_status.json")
        self.assertEqual(status["external_checker"], "NOT_RUN")
        self.assertFalse(status["external_checker_ran"])
        self.assertFalse(status["external_checker_verified"])
        self.assertNotEqual(status.get("external_checker_exit_code"), 0)
        print("DRAT_TRIM_CLAIM_GUARD_PASS")

    def test_drat_status_bundle_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dimacs = root / "unit_unsat.dimacs"
            write_dimacs(dimacs, [[1], [-1]], 1)
            cert = root / "unit.wcert"
            export_cert(dimacs, cert)
            status_path = cert / "drat_status.json"
            status = read_json(status_path)
            status["external_checker"] = "DRAT_TRIM"
            status["external_checker_ran"] = True
            status["external_checker_verified"] = True
            status["external_checker_exit_code"] = 0
            status_path.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            checked = verify_wcert_raw(cert)
        self.assertFalse(checked["verified"])
        self.assertEqual(checked["failed_check"], "file_hashes")
        print("DRAT_STATUS_BUNDLE_HASH_PASS")


if __name__ == "__main__":
    unittest.main()
