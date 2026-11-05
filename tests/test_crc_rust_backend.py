"""R-001: native Rust indexed VE versus Python, independent brute count."""
from __future__ import annotations

import os
import random
import unittest

from scripts.benchmark_crc_adversarial import chain_source, ring_source
from tests.test_crc_cutset_count import brute_models
from tests.test_crc_variable_elimination import fibonacci
from witnora_core.crc_boundary import _normalized_clauses
from witnora_core.crc_cutset_count import count_source_by_separator
from witnora_core.crc_rust_bridge import count_component_by_rust_elimination
from witnora_core.crc_variable_elimination_indexed import (
    count_component_by_indexed_elimination,
)


def rust(source, boundary, **kwargs):
    return count_component_by_rust_elimination(
        _normalized_clauses(source, boundary), boundary, **kwargs)


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "native Rust binary not configured (run Rust workflow)")
class TestRustVariableElimination(unittest.TestCase):
    def test_150_random_signed_source_and_operation_differentials(self):
        rng = random.Random(20020)
        checked = 0
        for n in (4, 5, 6, 7, 8):
            boundary = tuple(range(1, n + 1))
            for _ in range(30):
                source = []
                for _ in range(rng.randrange(12)):
                    variables = rng.sample(boundary, rng.randrange(1, 4))
                    source.append(tuple(
                        v if rng.randrange(2) else -v for v in variables))
                clauses = _normalized_clauses(source, boundary)
                python = count_component_by_indexed_elimination(
                    clauses, boundary, max_factor_variables=8)
                native = count_component_by_rust_elimination(
                    clauses, boundary, max_factor_variables=8)
                self.assertIsNotNone(python)
                self.assertIsNotNone(native)
                self.assertEqual(native.models, python.models)
                self.assertEqual(native.models, brute_models(source, n))
                self.assertEqual(native.operations, python.operations)
                self.assertEqual(native.max_factor_variables,
                                 python.max_factor_variables)
                checked += 1
        self.assertEqual(checked, 150)

    def test_large_fibonacci_and_lucas_bigints(self):
        for n in (16, 64, 128, 256):
            boundary = tuple(range(1, n + 1))
            for source, expected in (
                (chain_source(n), fibonacci(n + 2)),
                (ring_source(n), fibonacci(n - 1) + fibonacci(n + 1)),
            ):
                got = rust(source, boundary, max_factor_variables=3,
                           max_operations=200000)
                self.assertIsNotNone(got)
                self.assertEqual(got.models, expected)
                self.assertLessEqual(got.max_factor_variables, 3)

    def test_cutset_integration_exact_and_operations(self):
        for n in (16, 32, 64):
            boundary = tuple(range(1, n + 1))
            for source, left, right in (
                (chain_source(n), (1,), (n,)),
                (ring_source(n), (1,), (n // 2,)),
            ):
                kwargs = dict(
                    component_backend="variable_elimination_rust",
                    max_ve_factor_variables=3, max_ve_operations=200000,
                    max_separator_size=2)
                native = count_source_by_separator(
                    source, boundary, left, right, (1 << n) - 1, **kwargs)
                reference = count_source_by_separator(
                    source, boundary, left, right, (1 << n) - 1,
                    component_backend="variable_elimination_indexed",
                    max_ve_factor_variables=3, max_ve_operations=200000,
                    max_separator_size=2)
                self.assertIsNotNone(native)
                self.assertIsNotNone(reference)
                self.assertEqual(native.models, reference.models)
                self.assertEqual(native.ve_operations, reference.ve_operations)

    def test_inprocess_extension_matches_explicit_cli(self):
        from witnora_ve import count_component_native
        self.assertTrue(callable(count_component_native))
        binary = os.environ["WITNORA_RUST_VE_BIN"]
        for n in (8, 64, 128):
            boundary = tuple(range(1, n + 1))
            clauses = _normalized_clauses(chain_source(n), boundary)
            native = count_component_by_rust_elimination(
                clauses, boundary, max_factor_variables=3)
            cli = count_component_by_rust_elimination(
                clauses, boundary, max_factor_variables=3,
                binary_path=binary)
            self.assertEqual(native, cli)

    def test_fail_closed_and_invalid_masks(self):
        boundary = tuple(range(1, 17))
        clauses = _normalized_clauses(ring_source(16), boundary)
        self.assertIsNone(count_component_by_rust_elimination(
            clauses, boundary, max_factor_variables=2))
        self.assertIsNone(count_component_by_rust_elimination(
            clauses, boundary, max_operations=4))
        with self.assertRaises(ValueError):
            count_component_by_rust_elimination([(1 << 17, 0)], boundary)
        self.assertEqual(count_component_by_rust_elimination(
            (), (1, 2, 3), max_factor_variables=1).models, 8)


if __name__ == "__main__":
    unittest.main()
