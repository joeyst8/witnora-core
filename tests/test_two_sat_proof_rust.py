"""R-021 complete 2-SAT SCC metadata and certificate-log parity."""
from __future__ import annotations

import os
import random
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.certificate import StepLogger
from witnora_core.two_sat import solve_2sat


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestRustTwoSatProof(unittest.TestCase):
    def test_1000_full_scc_details_and_certificate_differentials(self):
        rng = random.Random(21212026)
        for n in range(1, 11):
            for _ in range(100):
                raw = [
                    [rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                     for _ in range(rng.randrange(3))]
                    for _ in range(rng.randrange(15))
                ]
                formula = CNFFormula(raw)
                with self.subTest(n=n, source=raw):
                    pylog, rustlog = StepLogger(), StepLogger()
                    py = solve_2sat(formula, pylog)
                    rust = solve_2sat(formula, rustlog, backend="rust_proof")
                    self.assertEqual(rust, py)
                    self.assertEqual(rustlog.steps, pylog.steps)

    def test_empty_conflict_units_and_three_clause_rejection(self):
        for raw in ([], [[]], [[1], [-1]], [[1], [-1, 2]],
                    [[1, 2], [-1, -2]]):
            formula = CNFFormula(raw)
            self.assertEqual(
                solve_2sat(formula),
                solve_2sat(formula, backend="rust_proof"))
        with self.assertRaises(ValueError):
            solve_2sat(CNFFormula([[1, 2, 3]]), backend="rust_proof")


if __name__ == "__main__":
    unittest.main()
