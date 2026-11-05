"""R-010 native Kosaraju two-SAT differential and witness tests."""
from __future__ import annotations

import os
import random
import unittest

from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.two_sat import solve_2sat
from witnora_core.two_sat_rust import solve_two_sat_in_rust


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestRustTwoSat(unittest.TestCase):
    def test_1600_seeded_random_cnfs_vs_original(self):
        rng = random.Random(10102026)
        for n in range(1, 9):
            for _ in range(200):
                clauses = []
                for _ in range(rng.randrange(16)):
                    clauses.append([
                        rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                        for _ in range(rng.randrange(3))
                    ])
                formula = CNFFormula.from_raw_clauses(clauses)
                with self.subTest(clauses=clauses, n=n):
                    python = solve_2sat(formula)
                    rust = solve_2sat(formula, backend="rust")
                    self.assertEqual(python["status"], rust["status"])
                    if rust["status"] == "SAT":
                        self.assertTrue(formula_satisfied(
                            formula, rust["assignment"]))
                    self.assertEqual(rust, solve_two_sat_in_rust(formula))

    def test_large_implication_chains_empty_and_unsat(self):
        n = 256
        chain = [[1]]
        for v in range(1, n):
            chain.append([-v, v + 1])
        source = CNFFormula.from_raw_clauses(chain)
        got = solve_2sat(source, backend="rust")
        self.assertEqual(got["status"], "SAT")
        self.assertEqual(sum(got["assignment"].values()), n)
        contradictory = CNFFormula.from_raw_clauses(chain + [[-n]])
        self.assertEqual(
            solve_2sat(contradictory, backend="rust")["status"], "UNSAT")
        self.assertEqual(
            solve_2sat(CNFFormula([[]]), backend="rust")["status"], "UNSAT")
        self.assertEqual(
            solve_2sat(CNFFormula(), backend="rust")["status"], "SAT")

    def test_strict_proof_boundary_and_non_2cnf(self):
        with self.assertRaisesRegex(ValueError, "proof logs"):
            solve_2sat(CNFFormula([[1]]), logger=object(), backend="rust")
        with self.assertRaisesRegex(ValueError, "2-CNF"):
            solve_2sat(CNFFormula([[1, 2, 3]]), backend="rust")
        with self.assertRaisesRegex(ValueError, "unknown"):
            solve_2sat(CNFFormula(), backend="invented")


if __name__ == "__main__":
    unittest.main()
