"""Frozen source-bound ETH-style clause-violation parity-sketch diagnostics."""
from __future__ import annotations

from dataclasses import replace
import unittest

from scripts.generate_glucose_dense_3sat_lean import find_case
from witnora_core.eth_clause_violation_parity import (
    build_finite_sketch, parity_accepts, verify_finite_sketch, violation_mask
)


class ClauseViolationParityTests(unittest.TestCase):
    def test_sparse_exact_separation_of_dense_3sat_controls(self) -> None:
        for nvars, nclauses in ((8, 54), (10, 66), (12, 84)):
            for planted in (False, True):
                with self.subTest(nvars=nvars, planted=planted):
                    source, info = find_case(nvars, nclauses, planted=planted)
                    sketch = build_finite_sketch(source, nvars)
                    self.assertTrue(verify_finite_sketch(source, sketch))
                    self.assertEqual(sketch.clause_count, nclauses)
                    self.assertEqual(sketch.survivors[-1], 0)
                    self.assertLessEqual(len(sketch.rows), 3 * nvars)
                    self.assertTrue(all(2 <= len(row) <= 5 for row in sketch.rows))
                    self.assertEqual(sketch.satisfying_count > 0, planted)
                    self.assertEqual(info["seed"], 630000 + 1000 * nvars
                                     + (100000 if planted else 0))

    def test_source_or_row_tampering_fails(self) -> None:
        source = [[1], [2]]
        sketch = build_finite_sketch(source, 2)
        self.assertTrue(verify_finite_sketch(source, sketch))
        self.assertFalse(verify_finite_sketch([[-1], [2]], sketch))
        self.assertFalse(verify_finite_sketch(source, replace(sketch, rows=((2,),))))
        self.assertFalse(verify_finite_sketch(source, replace(sketch, rows=((0, 0),))))
        self.assertFalse(verify_finite_sketch(source, replace(sketch, rows=())))

    def test_two_violated_clauses_can_cancel(self) -> None:
        source = ((1,), (2,))
        violations = violation_mask(source, assignment_bits=0)
        self.assertEqual(violations, 3)
        self.assertTrue(parity_accepts(violations, ((0, 1),)))
        sketch = build_finite_sketch(source, 2)
        self.assertFalse(verify_finite_sketch(source, replace(sketch, rows=((0, 1),))))

    def test_bounded_experiment_and_invalid_input(self) -> None:
        with self.assertRaises(ValueError):
            build_finite_sketch([[1]], 15)
        with self.assertRaises(ValueError):
            build_finite_sketch([[0]], 2)
        with self.assertRaises(ValueError):
            build_finite_sketch([[3]], 2)
        with self.assertRaises(ValueError):
            build_finite_sketch([[1], [2]], 2, max_rows=0)


if __name__ == "__main__":
    unittest.main()
