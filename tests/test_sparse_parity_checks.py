"""Nonenumerative sparse odd-column coding and adversarial collision tests."""
from __future__ import annotations

from dataclasses import replace
import unittest
from unittest.mock import patch

from scripts.generate_glucose_dense_3sat_lean import find_case, random_three_cnf
from witnora_core.eth_clause_violation_parity import source_digest
from witnora_core.sparse_parity_checks import (
    SparseOddSketch, audit_sparse_small, build_sparse_odd_sketch,
    column_signatures, low_weight_collisions, validate_sparse_odd_sketch,
    min_degree_elimination_width,
)


class SparseOddTests(unittest.TestCase):
    def test_all_six_source_bound_dense_cnf_controls(self) -> None:
        for nvars, nclauses in ((8, 54), (10, 66), (12, 84)):
            for planted in (False, True):
                with self.subTest(nvars=nvars, planted=planted):
                    cnf, _ = find_case(nvars, nclauses, planted=planted)
                    sketch = build_sparse_odd_sketch(cnf, nvars, seed=73)
                    validate_sparse_odd_sketch(cnf, sketch)
                    signatures = column_signatures(sketch.rows, nclauses)
                    self.assertEqual(len(signatures), len(set(signatures)))
                    self.assertTrue(all(s.bit_count() == 3 for s in signatures))
                    self.assertTrue(all(len(row) <= 5 for row in sketch.rows))
                    self.assertEqual(low_weight_collisions(sketch), 0)
                    profile = audit_sparse_small(cnf, sketch)
                    self.assertEqual(profile.source_models > 0, planted)
                    self.assertLessEqual(profile.max_scope_variables, 15)

    def test_builder_does_not_evaluate_assignments_even_at_96_vars(self) -> None:
        cnf = random_three_cnf(96, 576, 638000, planted=True)
        with patch("witnora_core.sparse_parity_checks.violation_mask",
                   side_effect=AssertionError("enumerated assignments")):
            sketch = build_sparse_odd_sketch(cnf, 96, seed=73)
        self.assertEqual(sketch, build_sparse_odd_sketch(cnf, 96, seed=73))
        validate_sparse_odd_sketch(cnf, sketch)
        self.assertTrue(all(len(row) <= 5 for row in sketch.rows))
        with self.assertRaises(ValueError):
            audit_sparse_small(cnf, sketch)

    def test_four_violation_collision_despite_perfect_1_to_3_detection(self) -> None:
        cnf = ((1,), (2,), (3,), (4,))
        # Four distinct degree-3 columns sum to zero over GF(2).
        rows = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))
        sketch = SparseOddSketch(4, 4, source_digest(cnf), 2, rows)
        validate_sparse_odd_sketch(cnf, sketch)
        self.assertEqual(low_weight_collisions(sketch), 0)
        self.assertGreater(audit_sparse_small(cnf, sketch).false_positives, 0)

    def test_min_degree_width_distinguishes_chain_and_clique(self) -> None:
        self.assertEqual(min_degree_elimination_width(
            [{1, 2}, {2, 3}, {3, 4}], 4), 1)
        self.assertEqual(min_degree_elimination_width(
            [{1, 2, 3, 4}], 4), 3)
        with self.assertRaises(ValueError):
            min_degree_elimination_width([{0, 1}], 4)

    def test_tampered_source_degree_and_row_capacity_rejected(self) -> None:
        cnf = [[1], [2], [3], [4], [5]]
        sketch = build_sparse_odd_sketch(cnf, 5, max_row_width=2)
        validate_sparse_odd_sketch(cnf, sketch)
        with self.assertRaises(ValueError):
            validate_sparse_odd_sketch([[-1], [2], [3], [4], [5]], sketch)
        with self.assertRaises(ValueError):
            validate_sparse_odd_sketch(cnf, replace(sketch, rows=sketch.rows[1:]))
        with self.assertRaises(ValueError):
            validate_sparse_odd_sketch(cnf, replace(sketch, max_row_width=1))
        with self.assertRaises(ValueError):
            build_sparse_odd_sketch(cnf, 5, max_row_width=0)


if __name__ == "__main__":
    unittest.main()
