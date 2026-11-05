"""R-019 complete native mathematical simplifier path and proof-log parity."""
from __future__ import annotations

import os
import random
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.certificate import StepLogger
from witnora_core.simplify import (
    _unit_step, _pure_literal_step, simplify,
)


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestRustSimplifier(unittest.TestCase):
    def test_1000_seeded_unit_pure_and_full_certificate_differentials(self):
        rng = random.Random(19192026)
        for n in range(1, 11):
            for _ in range(100):
                raw = [
                    [rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                     for _ in range(rng.randrange(5))]
                    for _ in range(rng.randrange(15))
                ]
                formula = CNFFormula(raw)
                with self.subTest(n=n, source=raw):
                    self.assertEqual(
                        _unit_step(formula, backend="rust"),
                        _unit_step(formula, backend="python"))
                    self.assertEqual(
                        _pure_literal_step(formula, backend="rust"),
                        _pure_literal_step(formula, backend="python"))
                    python_logger = StepLogger()
                    rust_logger = StepLogger()
                    py = simplify(
                        formula, python_logger,
                        log_component_decomposition=True)
                    rust = simplify(
                        formula, rust_logger,
                        log_component_decomposition=True,
                        backend="rust")
                    self.assertEqual(rust, py)
                    self.assertEqual(rust_logger.steps, python_logger.steps)

    def test_conflicting_units_pure_literals_and_multicomponent_event(self):
        for source in (
            [[1], [-1]],
            [[1, 2], [3]],
            [[1], [-1, 2], [-2]],
            [[1, -2], [-1, 2], [3, 4]],
        ):
            formula = CNFFormula(source)
            pylog, rustlog = StepLogger(), StepLogger()
            self.assertEqual(
                simplify(formula, pylog),
                simplify(formula, rustlog, backend="rust"))
            self.assertEqual(pylog.steps, rustlog.steps)

    def test_bad_backend(self):
        with self.assertRaises(ValueError):
            simplify(CNFFormula(), StepLogger(), backend="fake")


if __name__ == "__main__":
    unittest.main()
