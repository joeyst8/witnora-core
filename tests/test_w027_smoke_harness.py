"""Offline differential checks for cost-inclusive W027 smoke orchestration."""
import subprocess
import tempfile
from pathlib import Path
import unittest

from scripts.benchmark_w027_smoke import classify_solver, parse_dimacs, validate_model


class SmokeHarnessTests(unittest.TestCase):
    def test_solver_status_and_model_validation(self):
        self.assertEqual(classify_solver(subprocess.CompletedProcess([], 10, "s SATISFIABLE\nv 1 -2 0\n", "")), "SAT")
        self.assertEqual(classify_solver(subprocess.CompletedProcess([], 20, "s UNSATISFIABLE\n", "")), "UNSAT")
        self.assertEqual(classify_solver(subprocess.CompletedProcess([], 1, "s SATISFIABLE\n", "")), "ERROR")
        clauses = [[1, 2], [-1, -2]]
        self.assertTrue(validate_model(clauses, "v 1 -2 0\n"))
        self.assertFalse(validate_model(clauses, "v 1 2 0\n"))
        self.assertFalse(validate_model(clauses, "s SATISFIABLE\n"))

    def test_independent_dimacs_parser(self):
        with tempfile.TemporaryDirectory(prefix="w027-harness-") as directory:
            file = Path(directory) / "test.cnf"
            file.write_text("c comment\np cnf 3 2\n1 -2\n3 0\n-1 0\n")
            self.assertEqual(parse_dimacs(file), (3, [[1, -2, 3], [-1]]))


if __name__ == "__main__":
    unittest.main()
