"""Symbolic violation-image ANF semantics, cancellation and bounded counting."""
from __future__ import annotations

import unittest

from scripts.generate_glucose_dense_3sat_lean import random_three_cnf
from tests.test_exact_tensor_counting import collision_sketch
from witnora_core.aux_violation_tensors import (
    auxiliary_weight_profile_small, exact_source_models_small,
)
from witnora_core.eth_clause_violation_parity import violation_mask
from witnora_core.geometry_aware_parity import geometry_aware_sparse_sketch
from witnora_core.gf2_sparse_row_basis import build_sparse_parity_basis
from witnora_core.violation_image_anf import (
    ANFCountingBudgetExceeded, ONE, ZERO, analyze_parity_anf,
    clause_violation_polynomial, count_common_zeros,
    evaluate_polynomial, multiply_polynomials,
    row_violation_polynomials, source_violation_polynomials,
    variable, xor_polynomials,
)


class ViolationImageANFTests(unittest.TestCase):
    def test_boolean_ring_idempotency_and_tautology(self) -> None:
        x = variable(1)
        self.assertEqual(multiply_polynomials(x, x), x)
        self.assertEqual(clause_violation_polynomial([1, -1]), ZERO)
        self.assertEqual(clause_violation_polynomial([1, 1]),
                         xor_polynomials(ONE, x))
        self.assertEqual(clause_violation_polynomial([-1, -1]), x)
        self.assertEqual(clause_violation_polynomial([]), ONE)
        self.assertEqual(count_common_zeros(
            (clause_violation_polynomial([1, -1]),), 1).satisfying_assignments, 2)

    def test_clause_and_row_semantics_against_independent_evaluator(self) -> None:
        n, m = 5, 7
        source = random_three_cnf(n, m, 730005, planted=True)
        sketch = geometry_aware_sparse_sketch(source, n)
        clauses = source_violation_polynomials(source, n)
        equations = row_violation_polynomials(source, sketch)
        for assignment in range(1 << n):
            violations = violation_mask(tuple(map(tuple, source)), assignment)
            for j, eq in enumerate(clauses):
                self.assertEqual(evaluate_polynomial(eq, assignment),
                                 bool(violations & (1 << j)))
            for row, eq in zip(sketch.rows, equations):
                self.assertEqual(
                    evaluate_polynomial(eq, assignment),
                    sum(bool(violations & (1 << j)) for j in row) % 2 == 1)

    def test_exact_counts_and_parity_collisions_are_distinct(self) -> None:
        source, sketch = collision_sketch()
        direct = source_violation_polynomials(source, 4)
        parity = row_violation_polynomials(source, sketch)
        self.assertEqual(count_common_zeros(direct, 4).satisfying_assignments, 1)
        self.assertEqual(count_common_zeros(parity, 4).satisfying_assignments, 2)
        self.assertEqual(sum(auxiliary_weight_profile_small(
            source, sketch).coefficients), 2)

    def test_planted_small_counts_and_sparse_basis_equations(self) -> None:
        for n, m in ((4, 5), (5, 7), (6, 9)):
            with self.subTest(n=n):
                source = random_three_cnf(n, m, 730000 + n, planted=True)
                sketch = geometry_aware_sparse_sketch(source, n)
                basis = build_sparse_parity_basis(sketch)
                direct = source_violation_polynomials(source, n)
                parity = row_violation_polynomials(source, sketch)
                reduced = row_violation_polynomials(source, sketch, basis=basis)
                source_count = count_common_zeros(direct, n)
                parity_count = count_common_zeros(parity, n)
                basis_count = count_common_zeros(reduced, n)
                self.assertEqual(source_count.satisfying_assignments,
                                 exact_source_models_small(source, n))
                self.assertEqual(parity_count.satisfying_assignments,
                                 sum(auxiliary_weight_profile_small(
                                     source, sketch).coefficients))
                self.assertEqual(basis_count.satisfying_assignments,
                                 parity_count.satisfying_assignments)

    def test_budget_and_large_symbolic_construction(self) -> None:
        with self.assertRaises(ANFCountingBudgetExceeded):
            count_common_zeros(
                (clause_violation_polynomial([1, 2, 3]),),
                3, max_states=1)
        source = random_three_cnf(96, 576, 630096, planted=True)
        sketch = geometry_aware_sparse_sketch(source, 96)
        profile = analyze_parity_anf(source, sketch)
        self.assertEqual(profile.clause_count, 576)
        self.assertLessEqual(profile.reduced_row_monomials,
                             profile.raw_row_monomial_occurrences)
        self.assertLessEqual(profile.maximum_degree, 3)
        # No 2**96 assignment enumeration is involved.


if __name__ == "__main__":
    unittest.main()
