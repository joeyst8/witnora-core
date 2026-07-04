import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

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
    return code, json.loads(stdout.getvalue()), json.loads(
        (cert / "drat_status.json").read_text(encoding="utf-8")
    )


def ve_unsat_clauses():
    return [
        [1, 2, 3],
        [1, 2, -3],
        [1, -2, 3],
        [1, -2, -3],
        [-1, 2, 3],
        [-1, 2, -3],
        [-1, -2, 3],
        [-1, -2, -3],
    ]


def bce_then_ve_unsat_clauses():
    return ve_unsat_clauses() + [
        [4, 5, 6],
        [-4, -5],
        [-4, -6],
        [3, 4],
    ]


@unittest.skipUnless(real_drat_trim_path(), "real drat-trim not available on PATH or WITNORA_DRAT_TRIM")
class RealDRATTrimSmokeTest(unittest.TestCase):
    def assert_real_external_verified(self, status):
        self.assertEqual(status["external_checker"], "DRAT_TRIM")
        self.assertTrue(status["external_checker_ran"])
        self.assertTrue(status["external_checker_verified"], status)
        self.assertEqual(status["external_checker_exit_code"], 0)
        self.assertEqual(status["proof_scope"], "END_TO_END_FROM_ORIGINAL_CNF")

    def test_real_drat_trim_explicit_unit_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, result, status = export_with_real_drat_trim(
                Path(tmp),
                "unit_unsat",
                [[1], [-1]],
                1,
                real_drat_trim_path(),
            )
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "UNSAT")
        self.assert_real_external_verified(status)
        print("REAL_DRAT_TRIM_UNIT_CONFLICT_PASS")

    def test_real_drat_trim_ve_unsat(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, result, status = export_with_real_drat_trim(
                Path(tmp),
                "ve_unsat",
                ve_unsat_clauses(),
                3,
                real_drat_trim_path(),
            )
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "UNSAT")
        self.assert_real_external_verified(status)
        print("REAL_DRAT_TRIM_VE_UNSAT_PASS")

    def test_real_drat_trim_bce_ve_unsat(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, result, status = export_with_real_drat_trim(
                Path(tmp),
                "bce_ve_unsat",
                bce_then_ve_unsat_clauses(),
                6,
                real_drat_trim_path(),
            )
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "UNSAT")
        self.assert_real_external_verified(status)
        print("REAL_DRAT_TRIM_BCE_VE_UNSAT_PASS")


if __name__ == "__main__":
    unittest.main()
