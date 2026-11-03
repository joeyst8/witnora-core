"""Exact separator-conditioning semantics and search-failure controls."""
from __future__ import annotations

import unittest

from scripts.generate_glucose_dense_3sat_lean import random_three_cnf
from tests.test_exact_tensor_counting import collision_sketch
from witnora_core.anf_separator_conditioning import (
    count_common_zeros_conditioned, find_bounded_separator,
    residual_component_sizes,
)
from witnora_core.anf_structured_counter import count_common_zeros_structured
from witnora_core.aux_violation_tensors import exact_source_models_small
from witnora_core.violation_image_anf import (
    ANFCountingBudgetExceeded, clause_violation_polynomial,
    row_violation_polynomials, source_violation_polynomials,
)


def bridge_case(nblocks: int, connectors: int) -> tuple[list[list[int]], int]:
    if connectors not in (1, 2) or nblocks < 2:
        raise ValueError("invalid test bridge shape")
    block = random_three_cnf(6, 9, 730006, planted=True)
    source = [
        [(abs(lit) + connectors + 6 * j) * (1 if lit > 0 else -1)
         for lit in clause]
        for j in range(nblocks) for clause in block
    ]
    for j in range(nblocks):
        source.append([1, connectors + 6 * j + 1])
        if connectors == 2:
            source.append([2, connectors + 6 * j + 2])
    return source, connectors + 6 * nblocks


def independent_bridge_oracle(nblocks: int, connectors: int) -> int:
    """Only enumerate assignments within the six-variable base block."""
    block = random_three_cnf(6, 9, 730006, planted=True)
    total = 0
    for mask in range(1 << connectors):
        additional = [[j + 1] for j in range(connectors)
                      if not (mask & (1 << j))]
        local_count = exact_source_models_small(block + additional, 6)
        total += local_count ** nblocks
    return total


class SeparatorConditioningTests(unittest.TestCase):
    def test_one_bridge_and_exact_three_block_count(self) -> None:
        source, n = bridge_case(3, 1)
        equations = source_violation_polynomials(source, n)
        selected, checks = find_bounded_separator(
            equations, n, max_separator_size=1)
        self.assertEqual(selected, (1,))
        self.assertGreater(checks, 0)
        result = count_common_zeros_conditioned(
            equations, n, max_separator_size=1)
        self.assertTrue(result.separator_found)
        self.assertEqual(result.branches, 2)
        self.assertGreater(result.total_component_splits, 0)
        self.assertEqual(result.satisfying_assignments,
                         independent_bridge_oracle(3, 1))
        self.assertEqual(result.satisfying_assignments,
                         count_common_zeros_structured(
                             equations, n, max_states=20_000)
                         .satisfying_assignments)

    def test_two_bridge_conditioning_and_max_separator_gate(self) -> None:
        source, n = bridge_case(3, 2)
        equations = source_violation_polynomials(source, n)
        no_single, _ = find_bounded_separator(
            equations, n, max_separator_size=1)
        self.assertIsNone(no_single)
        selected, checks = find_bounded_separator(
            equations, n, max_separator_size=2)
        self.assertEqual(selected, (1, 2))
        self.assertGreater(checks, 0)
        result = count_common_zeros_conditioned(
            equations, n, max_separator_size=2)
        self.assertEqual(result.branches, 4)
        self.assertEqual(result.satisfying_assignments,
                         independent_bridge_oracle(3, 2))

    def test_dense_no_separator_fallback_and_collision(self) -> None:
        wide = (clause_violation_polynomial(list(range(1, 8))),)
        selected, _ = find_bounded_separator(
            wide, 7, max_separator_size=2)
        self.assertIsNone(selected)
        result = count_common_zeros_conditioned(
            wide, 7, max_separator_size=2)
        self.assertFalse(result.separator_found)
        self.assertEqual(result.satisfying_assignments,
                         count_common_zeros_structured(wide, 7)
                         .satisfying_assignments)
        source, sketch = collision_sketch()
        direct = source_violation_polynomials(source, 4)
        parity = row_violation_polynomials(source, sketch)
        self.assertEqual(count_common_zeros_conditioned(
            direct, 4).satisfying_assignments, 1)
        self.assertEqual(count_common_zeros_conditioned(
            parity, 4).satisfying_assignments, 2)

    def test_full_budget_and_invalid_variables(self) -> None:
        source, n = bridge_case(3, 1)
        equations = source_violation_polynomials(source, n)
        with self.assertRaises(ANFCountingBudgetExceeded):
            count_common_zeros_conditioned(
                equations, n, max_states=1)
        with self.assertRaises(ValueError):
            count_common_zeros_conditioned(
                (clause_violation_polynomial([3]),), 2)
        with self.assertRaises(ValueError):
            find_bounded_separator(equations, n, max_candidate_checks=0)

    def test_component_graph_after_bridge_removal(self) -> None:
        scopes = (0b0011, 0b0110, 0b1100)
        self.assertEqual(residual_component_sizes(scopes, 0), (4,))
        self.assertEqual(residual_component_sizes(scopes, 0b0110),
                         (1, 1))


if __name__ == "__main__":
    unittest.main()
