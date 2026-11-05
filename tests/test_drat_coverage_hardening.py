import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from witnora_core.benchmark import (
    UNSAT_DRAT_EXPORTED_VERIFIED,
    UNSAT_NOT_EXTERNALLY_VERIFIED,
    enforce_unsat_external_verification,
)
from witnora_core.certificate import UNSAT
from witnora_core.drat_trim import find_drat_trim
from witnora_core.runner import main as runner_main


def real_drat_trim_path():
    return find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM"))


def write_dimacs(path, clauses, num_vars):
    lines = [f"p cnf {num_vars} {len(clauses)}"]
    for clause in clauses:
        lines.append(" ".join(str(lit) for lit in clause) + " 0")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_with_real_drat_trim(root, name, clauses, num_vars, drat_trim_path):
    dimacs = root / f"{name}.dimacs"
    cert = root / f"{name}.wcert"
    write_dimacs(dimacs, clauses, num_vars)
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        code = runner_main(
            [
                str(dimacs),
                "--c",
                "2",
                "--export-cert",
                str(cert),
                "--export-drat",
                "--drat-trim",
                str(drat_trim_path),
            ]
        )
    return (
        code,
        json.loads(stdout.getvalue()),
        json.loads((cert / "drat_status.json").read_text(encoding="utf-8")),
        (cert / "proof.drat").read_text(encoding="utf-8"),
    )


def assert_real_external_verified(testcase, status):
    testcase.assertEqual(status["drat_export_status"], "EXPORTED")
    testcase.assertEqual(status["proof_scope"], "END_TO_END_FROM_ORIGINAL_CNF")
    testcase.assertEqual(status["checked_against"], "original.dimacs")
    testcase.assertEqual(status["external_checker"], "DRAT_TRIM")
    testcase.assertTrue(status["external_checker_ran"])
    testcase.assertTrue(status["external_checker_verified"], status)
    testcase.assertEqual(status["external_checker_exit_code"], 0)
    testcase.assertIn("VERIFIED", status["external_checker_stdout_excerpt"])


@unittest.skipUnless(real_drat_trim_path(), "real drat-trim not available on PATH or WITNORA_DRAT_TRIM")
class DRATCoverageHardeningRealSmokeTest(unittest.TestCase):
    def test_real_drat_trim_subsumption(self):
        clauses = [
            [1, 2],
            [1, -2],
            [-1, 2],
            [-1, -2],
            [1, 2, 3],
            [1, 2, -3],
        ]
        with tempfile.TemporaryDirectory() as tmp:
            code, result, status, proof = export_with_real_drat_trim(
                Path(tmp),
                "subsumption_unsat",
                clauses,
                3,
                real_drat_trim_path(),
            )
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "UNSAT")
        self.assertIn("SUB", [step["type"] for step in result["collapse_path"]])
        self.assertIn("d -3 1 2 0", proof)
        assert_real_external_verified(self, status)
        print("REAL_DRAT_TRIM_SUBSUMPTION_PASS")

    def test_real_drat_trim_ple(self):
        clauses = [
            [1, 2],
            [1, -2],
            [-1, 2],
            [-1, -2],
            [1, 2, 3],
        ]
        with tempfile.TemporaryDirectory() as tmp:
            code, result, status, proof = export_with_real_drat_trim(
                Path(tmp),
                "ple_unsat",
                clauses,
                3,
                real_drat_trim_path(),
            )
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "UNSAT")
        self.assertIn("PLE", [step["type"] for step in result["collapse_path"]])
        self.assertIn("d 1 2 3 0", proof)
        assert_real_external_verified(self, status)
        print("REAL_DRAT_TRIM_PLE_PASS")

    def test_real_drat_trim_multi_component_unsat(self):
        clauses = [[1], [-1], [2], [-2]]
        with tempfile.TemporaryDirectory() as tmp:
            code, result, status, proof = export_with_real_drat_trim(
                Path(tmp),
                "multi_component_unsat",
                clauses,
                2,
                real_drat_trim_path(),
            )
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "UNSAT")
        self.assertIn("CD", [step["type"] for step in result["collapse_path"]])
        self.assertEqual(proof.strip().splitlines()[-1], "0")
        assert_real_external_verified(self, status)
        print("REAL_DRAT_TRIM_MULTI_COMPONENT_UNSAT_PASS")


class BenchmarkExternalVerificationGuardTest(unittest.TestCase):
    def test_benchmark_unsat_external_verification_guard(self):
        verified_status = {
            "drat_export_status": "EXPORTED",
            "external_checker": "DRAT_TRIM",
            "external_checker_ran": True,
            "external_checker_verified": True,
        }
        unverified_status = {
            "drat_export_status": "EXPORTED",
            "external_checker": "NOT_RUN",
            "external_checker_ran": False,
            "external_checker_verified": False,
        }
        self.assertEqual(
            enforce_unsat_external_verification(UNSAT, verified_status),
            UNSAT_DRAT_EXPORTED_VERIFIED,
        )
        self.assertEqual(
            enforce_unsat_external_verification(UNSAT, unverified_status),
            UNSAT_NOT_EXTERNALLY_VERIFIED,
        )
        with self.assertRaises(ValueError):
            enforce_unsat_external_verification(UNSAT, unverified_status, strict=True)
        self.assertIsNone(enforce_unsat_external_verification("SAT", None, strict=True))
        print("BENCHMARK_UNSAT_EXTERNAL_VERIFICATION_GUARD_PASS")


if __name__ == "__main__":
    unittest.main()
