"""W-CRC-014 exact variable elimination and cutset integration controls."""
from __future__ import annotations

import random
import unittest

from scripts.benchmark_crc_adversarial import chain_source, ring_source
from tests.test_crc_cutset_count import brute_models
from witnora_core.crc_boundary import _normalized_clauses
from witnora_core.crc_cutset_count import count_source_by_separator
from witnora_core.crc_variable_elimination import (
    count_component_by_elimination,
)


def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


class TestCRCVariableElimination(unittest.TestCase):
    def test_160_random_exact_signed_differentials(self):
        rng = random.Random(14014)
        checked = 0
        for n in (4, 5, 6, 7):
            boundary = tuple(range(1, n + 1))
            for _ in range(40):
                source = []
                for _ in range(rng.randrange(0, 11)):
                    vars = rng.sample(boundary, rng.randrange(1, 4))
                    source.append([
                        v if rng.randrange(2) else -v for v in vars
                    ])
                normalized = _normalized_clauses(source, boundary)
                result = count_component_by_elimination(
                    normalized, boundary,
                    max_factor_variables=7, max_operations=1000000)
                self.assertIsNotNone(result)
                self.assertEqual(result.models, brute_models(source, n))
                checked += 1
        self.assertEqual(checked, 160)

    def test_chain_and_cycle_analytic_counts(self):
        for n in (8, 16, 32, 64):
            boundary = tuple(range(1, n + 1))
            for source, expected in (
                (chain_source(n), fibonacci(n + 2)),
                (ring_source(n), fibonacci(n - 1) + fibonacci(n + 1)),
            ):
                with self.subTest(n=n, edges=len(source)):
                    normalized = _normalized_clauses(source, boundary)
                    result = count_component_by_elimination(
                        normalized, boundary,
                        max_factor_variables=3, max_operations=50000)
                    self.assertIsNotNone(result)
                    self.assertEqual(result.models, expected)
                    self.assertLessEqual(result.max_factor_variables, 3)

    def test_fail_closed_width_work_and_masks(self):
        boundary = tuple(range(1, 9))
        normalized = _normalized_clauses(chain_source(8), boundary)
        self.assertIsNone(count_component_by_elimination(
            normalized, boundary, max_factor_variables=1))
        self.assertIsNone(count_component_by_elimination(
            normalized, boundary, max_operations=2))
        self.assertIsNone(count_component_by_elimination(
            _normalized_clauses([[1, 2, 3]], boundary),
            boundary, max_factor_variables=2))
        with self.assertRaises(ValueError):
            count_component_by_elimination([(1 << 8, 0)], boundary)
        with self.assertRaises(ValueError):
            count_component_by_elimination(normalized, boundary,
                                           max_factor_variables=0)
        with self.assertRaises(ValueError):
            count_component_by_elimination(normalized, boundary,
                                           max_operations=0)

    def test_cutset_chain_and_ring_become_admitted(self):
        for n in (16, 32, 64):
            boundary = tuple(range(1, n + 1))
            for source, groups, expected in (
                (chain_source(n), ((1,), (n,)), fibonacci(n + 2)),
                (ring_source(n), ((1,), (n // 2,)),
                 fibonacci(n - 1) + fibonacci(n + 1)),
            ):
                with self.subTest(n=n, edges=len(source)):
                    base = count_source_by_separator(
                        source, boundary, *groups, (1 << n) - 1,
                        max_separator_size=2, max_component_variables=8)
                    self.assertIsNone(base)
                    result = count_source_by_separator(
                        source, boundary, *groups, (1 << n) - 1,
                        max_separator_size=2, max_component_variables=8,
                        component_backend="variable_elimination",
                        max_ve_factor_variables=3,
                        max_ve_operations=100000)
                    self.assertIsNotNone(result)
                    self.assertEqual(result.models, expected)
                    self.assertGreater(result.max_residual_component, 8)
                    self.assertLessEqual(result.ve_max_factor_variables, 3)

    def test_seeded_integrated_random_comparisons(self):
        rng = random.Random(14015)
        admitted = 0
        for n in (6, 7, 8):
            boundary = tuple(range(1, n + 1))
            for _ in range(30):
                source = []
                for _ in range(rng.randrange(0, 10)):
                    vars = rng.sample(boundary, rng.randrange(1, 4))
                    signed = [v if rng.randrange(2) else -v for v in vars]
                    signed[0] = vars[0]
                    source.append(signed)
                result = count_source_by_separator(
                    source, boundary, (1,), (2,), (1 << n) - 1,
                    max_separator_size=2,
                    component_backend="variable_elimination",
                    max_ve_factor_variables=8)
                if result is None:
                    continue
                self.assertEqual(result.models, brute_models(source, n))
                admitted += 1
        self.assertGreater(admitted, 10)

    def test_api_rejects_unknown_backend_and_budget(self):
        source = chain_source(16)
        boundary = tuple(range(1, 17))
        with self.assertRaises(ValueError):
            count_source_by_separator(
                source, boundary, (1,), (16,), 65535,
                component_backend="approximate")
        self.assertIsNone(count_source_by_separator(
            source, boundary, (1,), (16,), 65535,
            component_backend="variable_elimination",
            max_ve_factor_variables=1))


if __name__ == "__main__":
    unittest.main()
