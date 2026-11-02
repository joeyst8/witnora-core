"""Offline regression checks for external benchmark integrity and timeouts."""
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.dimacs import parse_dimacs_with_raw
from witnora_core.xor import canonical_xor_cnf_clauses

from scripts.benchmark_real_satlib_parity_gate import (
    affine_obstruction, bounded_solve, fetch_file, SOLVERS,
)


class RealParityGateTests(unittest.TestCase):
    def test_strict_dimacs_evidence_keeps_original_clauses(self):
        raw = "c test\np cnf 3 3\n1 2 0\n1 2 0\n-3 0\n"
        formula, clauses = parse_dimacs_with_raw(raw)
        self.assertEqual(len(clauses), 3)
        self.assertEqual(len(formula.clauses), 2)
        self.assertEqual(clauses, [[1, 2], [1, 2], [-3]])

    def test_affine_residual_obstruction_counts(self):
        clauses = list(canonical_xor_cnf_clauses((1, 2, 3), 0))
        clauses.append((1,))
        formula = CNFFormula.from_raw_clauses(clauses)
        info = affine_obstruction(formula)
        self.assertEqual(info["verified_exact_xor_rows"], 1)
        self.assertTrue(info["xor_only_consistent"])
        self.assertEqual(info["residual_non_xor_clauses"], 1)
        self.assertEqual(info["residual_vars_touching_xor"], 1)
        self.assertEqual(info["projected_residual_support"]["residual_clause_count"], 1)
        self.assertEqual(info["projected_residual_support"]["max_coordinate_support"], 1)

    def test_native_solver_isolated_correctness(self):
        for name in SOLVERS:
            with self.subTest(name=name):
                self.assertEqual(bounded_solve([(1, 2), (-1, 2)], name, 2)["status"], "SAT")
                self.assertEqual(bounded_solve([(1,), (-1,)], name, 2)["status"], "UNSAT")

    def test_fail_closed_bad_source_or_budget(self):
        with self.assertRaises(ValueError):
            fetch_file("../other.cnf.Z", True)
        with self.assertRaises(ValueError):
            bounded_solve([(1,)], "unknown_backend", 1)
        with self.assertRaises(ValueError):
            bounded_solve([(1,)], SOLVERS[0], 0)


if __name__ == "__main__":
    unittest.main()
