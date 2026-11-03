"""Exactness and fail-closed checks for shared-cofactor ANF counting."""
from __future__ import annotations

import unittest

from scripts.generate_glucose_dense_3sat_lean import random_three_cnf
from tests.test_exact_tensor_counting import collision_sketch
from witnora_core.aux_violation_tensors import (
    auxiliary_weight_profile_small, exact_source_models_small,
)
from witnora_core.geometry_aware_parity import geometry_aware_sparse_sketch
from witnora_core.anf_structured_counter import count_common_zeros_structured
from witnora_core.violation_image_anf import (
    ANFCountingBudgetExceeded, ONE,
    clause_violation_polynomial, count_common_zeros,
    row_violation_polynomials, source_violation_polynomials,
)


class StructuredANFTests(unittest.TestCase):
    def test_independent_components_with_free_variable(self) -> None:
        # Each clause excludes one of four local assignments.
        eqs = (clause_violation_polynomial([1, 2]),
               clause_violation_polynomial([3, 4]))
        result = count_common_zeros_structured(eqs, 5)
        self.assertEqual(result.satisfying_assignments, 3 * 3 * 2)
        self.assertGreater(result.component_splits, 0)
        self.assertEqual(result.satisfying_assignments,
                         count_common_zeros(eqs, 5).satisfying_assignments)

    def test_forced_substitution_and_unconstrained_variables(self) -> None:
        eqs = (clause_violation_polynomial([-1]),
               clause_violation_polynomial([2]))
        result = count_common_zeros_structured(eqs, 4)
        self.assertEqual(result.satisfying_assignments, 4)
        self.assertGreaterEqual(result.forced_assignments, 2)
        self.assertEqual(count_common_zeros_structured((ONE,), 4)
                         .satisfying_assignments, 0)
        self.assertEqual(count_common_zeros_structured((), 96)
                         .satisfying_assignments, 1 << 96)

    def test_finite_oracles_for_source_and_parity(self) -> None:
        for n, m in ((4, 5), (5, 7), (6, 9)):
            source = random_three_cnf(n, m, 730000 + n, planted=True)
            sketch = geometry_aware_sparse_sketch(source, n)
            direct = source_violation_polynomials(source, n)
            parity = row_violation_polynomials(source, sketch)
            with self.subTest(n=n, kind="source"):
                result = count_common_zeros_structured(direct, n)
                self.assertEqual(result.satisfying_assignments,
                                 exact_source_models_small(source, n))
                self.assertEqual(result.satisfying_assignments,
                                 count_common_zeros(direct, n)
                                 .satisfying_assignments)
            with self.subTest(n=n, kind="parity"):
                result = count_common_zeros_structured(parity, n)
                self.assertEqual(result.satisfying_assignments,
                                 sum(auxiliary_weight_profile_small(
                                     source, sketch).coefficients))
                self.assertEqual(result.satisfying_assignments,
                                 count_common_zeros(parity, n)
                                 .satisfying_assignments)

    def test_adversarial_sketch_collision_not_hidden(self) -> None:
        source, sketch = collision_sketch()
        source_eq = source_violation_polynomials(source, 4)
        parity_eq = row_violation_polynomials(source, sketch)
        self.assertEqual(count_common_zeros_structured(
            source_eq, 4).satisfying_assignments, 1)
        self.assertEqual(count_common_zeros_structured(
            parity_eq, 4).satisfying_assignments, 2)

    def test_disjoint_block_product_against_finite_oracle(self) -> None:
        block = random_three_cnf(6, 9, 730006, planted=True)
        nblocks = 3
        extended = [[((abs(lit) + 6 * j) * (1 if lit > 0 else -1))
                     for lit in clause]
                    for j in range(nblocks) for clause in block]
        eqs = source_violation_polynomials(extended, 6 * nblocks)
        expected = exact_source_models_small(block, 6) ** nblocks
        result = count_common_zeros_structured(eqs, 6 * nblocks)
        self.assertEqual(result.satisfying_assignments, expected)
        self.assertGreater(result.component_splits, 0)

    def test_validation_and_search_budget(self) -> None:
        with self.assertRaises(ValueError):
            count_common_zeros_structured(
                (clause_violation_polynomial([3]),), 2)
        with self.assertRaises(ANFCountingBudgetExceeded):
            count_common_zeros_structured(
                (clause_violation_polynomial([1, 2, 3]),),
                3, max_states=1)


if __name__ == "__main__":
    unittest.main()
