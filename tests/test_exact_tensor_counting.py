"""Actual polynomial factor contraction: exact source/aux counting controls."""
from __future__ import annotations

import unittest

from scripts.generate_glucose_dense_3sat_lean import random_three_cnf
from witnora_core.aux_violation_tensors import (
    auxiliary_weight_profile_small, exact_source_models_small,
)
from witnora_core.eth_clause_violation_parity import source_digest
from witnora_core.exact_tensor_counting import (
    ContractionBudgetExceeded, auxiliary_factors, contract_factors,
    count_auxiliary_weight_polynomial, count_source_exact,
    poly_add, poly_mul,
)
from witnora_core.geometry_aware_parity import geometry_aware_sparse_sketch
from witnora_core.sparse_parity_checks import SparseOddSketch


def collision_sketch() -> tuple[list[list[int]], SparseOddSketch]:
    source = [[1], [2], [3], [4]]
    rows = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))
    sketch = SparseOddSketch(4, 4, source_digest(tuple(map(tuple, source))),
                             2, rows)
    return source, sketch


def normalized(p: tuple[int, ...], degree: int) -> tuple[int, ...]:
    return p + (0,) * max(0, degree - len(p))


class ExactTensorCountingTests(unittest.TestCase):
    def test_basic_polynomial_arithmetic(self) -> None:
        self.assertEqual(poly_add((1, 2), (3, 0, 4)), (4, 2, 4))
        self.assertEqual(poly_mul((1, 2), (3, 4)), (3, 10, 8))
        self.assertEqual(poly_mul((), (1,)), ())
        self.assertEqual(poly_add((1,), (-1,)), ())

    def test_exact_source_count_including_unused_variable(self) -> None:
        self.assertEqual(count_source_exact([[1]], 2).coefficients, (2,))
        self.assertEqual(count_source_exact([[1], [-1]], 1).coefficients, ())
        self.assertEqual(count_source_exact([[]], 2).coefficients, ())
        self.assertEqual(count_source_exact([], 2).coefficients, (4,))

    def test_three_variable_exact_aux_polynomial(self) -> None:
        source = [[1, 2, 3], [1, -2, 3], [-1, 2, 3]]
        sketch = geometry_aware_sparse_sketch(source, 3)
        result = count_auxiliary_weight_polynomial(source, sketch)
        oracle = auxiliary_weight_profile_small(source, sketch)
        self.assertEqual(normalized(result.coefficients, 4),
                         oracle.coefficients)
        self.assertEqual(result.coefficients[0],
                         count_source_exact(source, 3).coefficients[0])

    def test_adversarial_four_violation_collision_at_positive_degree(self) -> None:
        source, sketch = collision_sketch()
        contraction = count_auxiliary_weight_polynomial(source, sketch)
        oracle = auxiliary_weight_profile_small(source, sketch)
        self.assertEqual(normalized(contraction.coefficients, 5),
                         oracle.coefficients)
        self.assertEqual(contraction.coefficients, (1, 0, 0, 0, 1))
        self.assertEqual(count_source_exact(source, 4).coefficients, (1,))

    def test_random_four_variable_count(self) -> None:
        source = random_three_cnf(4, 5, 730004, planted=True)
        sketch = geometry_aware_sparse_sketch(source, 4)
        source_result = count_source_exact(source, 4)
        aux_result = count_auxiliary_weight_polynomial(source, sketch)
        oracle = auxiliary_weight_profile_small(source, sketch)
        self.assertEqual(normalized(aux_result.coefficients, len(oracle.coefficients)),
                         oracle.coefficients)
        self.assertEqual(source_result.coefficients[0],
                         exact_source_models_small(source, 4))
        self.assertEqual(aux_result.coefficients[0],
                         source_result.coefficients[0])

    def test_budget_fails_closed_and_invalid_order(self) -> None:
        with self.assertRaises(ContractionBudgetExceeded):
            count_source_exact([[1, 2]], 2, max_bucket_variables=1)
        factors = count_source_exact([[1]], 1)
        self.assertEqual(factors.coefficients, (1,))
        with self.assertRaises(ValueError):
            contract_factors([], 2, order=(1, 1))
        with self.assertRaises(ValueError):
            contract_factors([], 2, max_visited_assignments=0)


if __name__ == "__main__":
    unittest.main()
