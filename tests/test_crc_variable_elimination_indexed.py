"""W-CRC-015 indexed VE versus old exact VE and independent exhaustive #SAT."""
from __future__ import annotations

import random
import unittest

from scripts.benchmark_crc_adversarial import (
    chain_source, ring_source, block_source,
)
from tests.test_crc_cutset_count import brute_models
from witnora_core.crc_boundary import _normalized_clauses
from witnora_core.crc_cutset_count import count_source_by_separator
from witnora_core.crc_variable_elimination import count_component_by_elimination
from witnora_core.crc_variable_elimination_indexed import (
    count_component_by_indexed_elimination,
)
from tests.test_crc_variable_elimination import fibonacci


class TestIndexedVariableElimination(unittest.TestCase):
    def test_200_signed_random_reference_and_brute_differentials(self):
        rng = random.Random(15015)
        checked = 0
        for n in (4, 5, 6, 7, 8):
            boundary = tuple(range(1, n + 1))
            for _ in range(40):
                clauses = []
                for _ in range(rng.randrange(0, 12)):
                    vs = rng.sample(boundary, rng.randrange(1, 4))
                    clauses.append(tuple(
                        v if rng.randrange(2) else -v for v in vs))
                normalized = _normalized_clauses(clauses, boundary)
                baseline = count_component_by_elimination(
                    normalized, boundary,
                    max_factor_variables=8, max_operations=1000000)
                indexed = count_component_by_indexed_elimination(
                    normalized, boundary,
                    max_factor_variables=8, max_operations=1000000)
                self.assertIsNotNone(baseline)
                self.assertIsNotNone(indexed)
                expected = brute_models(clauses, n)
                self.assertEqual(indexed.models, expected)
                self.assertEqual(indexed.models, baseline.models)
                self.assertEqual(indexed.operations, baseline.operations)
                checked += 1
        self.assertEqual(checked, 200)

    def test_chain_and_ring_large_exact_analytic_counts(self):
        for n in (16, 32, 64, 128):
            boundary = tuple(range(1, n + 1))
            for source, expected in (
                (chain_source(n), fibonacci(n + 2)),
                (ring_source(n), fibonacci(n - 1) + fibonacci(n + 1)),
            ):
                with self.subTest(n=n, edges=len(source)):
                    normalized = _normalized_clauses(source, boundary)
                    indexed = count_component_by_indexed_elimination(
                        normalized, boundary,
                        max_factor_variables=3, max_operations=50000)
                    self.assertIsNotNone(indexed)
                    self.assertEqual(indexed.models, expected)
                    self.assertLessEqual(indexed.max_factor_variables, 3)

    def test_integrated_cutset_same_count_as_reference(self):
        for n in (16, 32, 64):
            boundary = tuple(range(1, n + 1))
            for source, groups in (
                (chain_source(n), ((1,), (n,))),
                (ring_source(n), ((1,), (n // 2,))),
            ):
                kw = dict(max_separator_size=2,
                          max_component_variables=8,
                          max_ve_factor_variables=3,
                          max_ve_operations=100000)
                old = count_source_by_separator(
                    source, boundary, *groups, (1 << n) - 1,
                    component_backend="variable_elimination", **kw)
                new = count_source_by_separator(
                    source, boundary, *groups, (1 << n) - 1,
                    component_backend="variable_elimination_indexed", **kw)
                self.assertIsNotNone(old)
                self.assertIsNotNone(new)
                self.assertEqual(new.models, old.models)
                self.assertEqual(new.ve_operations, old.ve_operations)
                self.assertEqual(new.component_backend,
                                 "variable_elimination_indexed")

    def test_signed_modular_blocks_and_empty_components(self):
        for blocks in (2, 4, 8):
            source, n, expected = block_source(blocks)
            got = count_source_by_separator(
                source, tuple(range(1, n + 1)), (1,), (4,),
                (1 << n) - 1, component_backend="variable_elimination_indexed",
                max_ve_factor_variables=4)
            self.assertIsNotNone(got)
            self.assertEqual(got.models, expected)
        empty = count_component_by_indexed_elimination(
            (), (1, 2, 3), max_factor_variables=1)
        self.assertEqual(empty.models, 8)

    def test_fail_closed_and_bad_mask(self):
        source = ring_source(16)
        norm = _normalized_clauses(source, tuple(range(1, 17)))
        self.assertIsNone(count_component_by_indexed_elimination(
            norm, tuple(range(1, 17)), max_factor_variables=2))
        self.assertIsNone(count_component_by_indexed_elimination(
            norm, tuple(range(1, 17)), max_operations=4))
        with self.assertRaises(ValueError):
            count_component_by_indexed_elimination(
                [(1 << 4, 0)], (1, 2, 3, 4))
        with self.assertRaises(ValueError):
            count_component_by_indexed_elimination(norm,
                tuple(range(1, 17)), max_factor_variables=0)


if __name__ == "__main__":
    unittest.main()
