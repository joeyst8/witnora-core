"""Dense, complete-primal-graph 3SAT controls for the Glucose→RUP gate."""
from __future__ import annotations

import unittest

from scripts.generate_glucose_dense_3sat_lean import (
    complete_primal_graph,
    find_case,
    random_three_cnf,
)
from witnora_core.rup_witness_import import verify_native_witness


class DenseRandom3SATTests(unittest.TestCase):
    def test_deterministic_distinct_three_literals_and_complete_graph(self) -> None:
        a = random_three_cnf(8, 54, 638000, planted=False)
        self.assertEqual(a, random_three_cnf(8, 54, 638000, planted=False))
        self.assertEqual(len(a), len({tuple(row) for row in a}))
        self.assertTrue(all(len(row) == 3 and len({abs(x) for x in row}) == 3 for row in a))
        self.assertTrue(complete_primal_graph([[1, 2, 3]], 3))
        self.assertFalse(complete_primal_graph([[1, 2, 3]], 4))

    def test_real_glucose_unsat_with_no_small_separator(self) -> None:
        raw, info = find_case(8, 54, planted=False)
        self.assertTrue(complete_primal_graph(raw, 8))
        self.assertEqual(info["status"], "LEAN_CHECK_PENDING")
        self.assertTrue(verify_native_witness(raw, info["proof"]["additions"]))
        self.assertFalse(verify_native_witness([], info["proof"]["additions"]))

    def test_real_glucose_sat_with_explicit_all_true_model(self) -> None:
        from pysat.solvers import Glucose3
        raw, info = find_case(8, 54, planted=True)
        self.assertTrue(complete_primal_graph(raw, 8))
        self.assertEqual(info["status"], "SAT_CONTROL")
        self.assertTrue(all(any(lit > 0 for lit in clause) for clause in raw))
        with Glucose3(bootstrap_with=raw) as solver:
            self.assertTrue(solver.solve())


if __name__ == "__main__":
    unittest.main()
