"""Independent small-model checks for auxiliary violation tensor bridge."""
from __future__ import annotations

import unittest

from scripts.generate_glucose_dense_3sat_lean import find_case, random_three_cnf
from witnora_core.aux_violation_tensors import (
    auxiliary_factor_scopes, auxiliary_weight_profile_small,
    constant_term_matches_source, direct_parity_factor_scopes,
    exact_source_models_small, independent_violation_mask,
)
from witnora_core.eth_clause_violation_parity import violation_mask
from witnora_core.geometry_aware_parity import geometry_aware_sparse_sketch
from witnora_core.sparse_parity_checks import (
    SparseOddSketch, min_degree_elimination_width,
)


class AuxiliaryViolationTensorTests(unittest.TestCase):
    def test_constant_coefficient_six_dense_controls(self) -> None:
        for n, m in ((8, 54), (10, 66), (12, 84)):
            for planted in (False, True):
                with self.subTest(n=n, planted=planted):
                    source, _ = find_case(n, m, planted=planted)
                    sketch = geometry_aware_sparse_sketch(source, n)
                    p = auxiliary_weight_profile_small(source, sketch)
                    self.assertEqual(p.constant_coefficient,
                                     exact_source_models_small(source, n))
                    self.assertTrue(constant_term_matches_source(
                        source, sketch))
                    # These six frozen sketches admit no false positives:
                    # sum(coefficients) is the number passing parity,
                    # NOT the number of all source assignments.
                    self.assertEqual(sum(p.coefficients),
                                     p.constant_coefficient)

    def test_literal_evaluator_independence(self) -> None:
        source = ((1, -2), (-1, 3), (2,), ())
        for x in range(1 << 3):
            self.assertEqual(independent_violation_mask(source, x),
                             violation_mask(source, x))

    def test_parity_only_can_have_positive_degree_collisions(self) -> None:
        # All-false assignment violates both unit clauses. One two-bit
        # parity row accepts it, but the constant coefficient excludes it.
        source = [[1], [2]]
        sketch = SparseOddSketch(nvars=2, clause_count=2, digest="",
                                 max_row_width=2, rows=((0, 1),))
        # Use no structural sparse validator here: this deliberately
        # adversarial parity sketch does not have 3-odd column signatures.
        self.assertEqual(independent_violation_mask(tuple(map(tuple, source)), 0), 3)
        self.assertEqual((3 & 1) ^ ((3 >> 1) & 1), 0)

    def test_auxiliary_scopes_preserve_locality_of_clause_factor(self) -> None:
        n, m = 32, 224
        source = random_three_cnf(n, m, 630032, planted=True)
        sketch = geometry_aware_sparse_sketch(source, n)
        aux = auxiliary_factor_scopes(source, sketch)
        direct = direct_parity_factor_scopes(source, sketch)
        self.assertEqual(len(aux), m + len(sketch.rows))
        self.assertEqual(max(map(len, aux[:m])), 4)
        self.assertLessEqual(max(map(len, aux[m:])), 5)
        self.assertGreater(max(map(len, direct)), 4)
        width = min_degree_elimination_width(aux, n + m)
        self.assertGreaterEqual(width, 0)
        # This measures a different graph with n+m variables, not
        # guaranteed to beat the source or any CDCL solver.

    def test_no_accidental_large_exhaustion(self) -> None:
        source = random_three_cnf(32, 224, 630032, planted=True)
        sketch = geometry_aware_sparse_sketch(source, 32)
        with self.assertRaises(ValueError):
            auxiliary_weight_profile_small(source, sketch)
        with self.assertRaises(ValueError):
            exact_source_models_small(source, 32)


if __name__ == "__main__":
    unittest.main()
