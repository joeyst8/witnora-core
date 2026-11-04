"""R-020 proof-aware variable elimination Rust differential checks."""
from __future__ import annotations

import os
import random
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.certificate import StepLogger
from witnora_core.ve import eliminate_variable, run_variable_elimination


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestRustProofVariableElimination(unittest.TestCase):
    def test_1000_seeded_exact_resolution_and_proof_event_differentials(self):
        rng = random.Random(20202026)
        for n in range(1, 11):
            for _ in range(100):
                raw = [
                    [rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                     for _ in range(rng.randrange(5))]
                    for _ in range(rng.randrange(14))
                ]
                formula = CNFFormula(raw)
                pivot = rng.randrange(1, n + 2)
                cap = rng.randrange(5)
                with self.subTest(n=n, source=raw, pivot=pivot, cap=cap):
                    pylog, rustlog = StepLogger(), StepLogger()
                    py = eliminate_variable(
                        formula, pivot, cap, pylog)
                    rust = eliminate_variable(
                        formula, pivot, cap, rustlog, backend="rust")
                    self.assertEqual(py, rust)
                    self.assertEqual(pylog.steps, rustlog.steps)

    def test_300_full_order_replays(self):
        rng = random.Random(20202226)
        for n in range(2, 8):
            for _ in range(50):
                source = [
                    [rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                     for _ in range(rng.randrange(4))]
                    for _ in range(rng.randrange(12))
                ]
                formula = CNFFormula(source)
                order = list(range(1, n + 1))
                rng.shuffle(order)
                cap = rng.randrange(5)
                pylog, rustlog = StepLogger(), StepLogger()
                py = run_variable_elimination(
                    formula, order, cap, pylog)
                rust = run_variable_elimination(
                    formula, order, cap, rustlog, backend="rust")
                with self.subTest(source=source, order=order, cap=cap):
                    self.assertEqual(py, rust)
                    self.assertEqual(pylog.steps, rustlog.steps)

    def test_tautological_resolvents_zero_width_and_refusals(self):
        for source, pivot, cap in (
            ([[1, 2], [-1, -2]], 1, 2),
            ([[1], [-1]], 1, 0),
            ([[1, 2], [-1, 3]], 1, 1),
            ([[1, 2]], 3, 0),
        ):
            formula = CNFFormula(source)
            self.assertEqual(eliminate_variable(formula, pivot, cap),
                             eliminate_variable(formula, pivot, cap, backend="rust"))

    def test_unknown_backend(self):
        with self.assertRaises(ValueError):
            eliminate_variable(CNFFormula(), 1, 0, backend="fake")


if __name__ == "__main__":
    unittest.main()
