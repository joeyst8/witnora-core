"""R-008: full one-call native Rust source-to-count differential checks."""
from __future__ import annotations

import os
import random
import unittest

from witnora_core.crc_rust_fused import count_source_fused_in_rust
from witnora_core.crc_source import _xor_cnf, count_signed_cnf_crc


def truth_count(clauses, n):
    count = 0
    for mask in range(1 << n):
        if all(any((mask >> (abs(lit) - 1) & 1) == (lit > 0)
                   for lit in clause) for clause in clauses):
            count += 1
    return count


def or_xor_groups(groups, xor_blocks):
    source = []
    for group in range(groups):
        triple = tuple(range(3 * group + 1, 3 * group + 4))
        source.append(triple)
        if group < xor_blocks:
            source.extend(_xor_cnf(triple, 0))
    return source, 3 * groups, 3 ** xor_blocks * 7 ** (groups - xor_blocks)


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestRustFusedSource(unittest.TestCase):
    def test_seeded_210_random_sources_each_three_preprocessing_modes(self):
        rng = random.Random(8082026)
        for n in range(2, 9):
            for _ in range(30):
                clauses = []
                for _ in range(rng.randrange(10)):
                    clauses.append([rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                                    for _ in range(rng.randrange(5))])
                expected = truth_count(clauses, n)
                for mode in ("none", "rust_consensus", "rust_adaptive"):
                    with self.subTest(n=n, clauses=clauses, mode=mode):
                        fused = count_signed_cnf_crc(
                            clauses, n, source_backend="rust_fused",
                            source_preprocessor=mode, max_inclusion_subsets=8192)
                        self.assertIsNotNone(fused)
                        self.assertEqual(fused.models, expected)
                        py = count_signed_cnf_crc(
                            clauses, n, max_inclusion_subsets=8192)
                        self.assertIsNotNone(py)
                        self.assertEqual(fused.models, py.models)
                        self.assertEqual(
                            fused.coefficient_stats.models, expected)

    def test_structured_exponential_exact_counts(self):
        for groups in (1, 2, 4, 8, 16, 20):
            for xor_blocks in (0, 1, 3, 6):
                if xor_blocks > groups:
                    continue
                clauses, n, expected = or_xor_groups(groups, xor_blocks)
                with self.subTest(groups=groups, xor_blocks=xor_blocks):
                    fused = count_source_fused_in_rust(
                        clauses, n, max_inclusion_subsets=512)
                    self.assertIsNotNone(fused)
                    self.assertEqual(fused.models, expected)
                    self.assertEqual(fused.boundary_variables +
                                     fused.internal_variables, n)

    def test_empty_contradictory_tautological_and_units(self):
        for clauses, n, expected in (
            ([], 0, 1), ([], 64, 1 << 64),
            ([[]], 3, 0),
            ([[1], [-1]], 4, 0),
            ([[1, -1]], 4, 16),
            ([[1], [1, 2]], 3, 4),
        ):
            with self.subTest(clauses=clauses, n=n):
                got = count_source_fused_in_rust(
                    clauses, n, source_preprocessor="none")
                self.assertIsNotNone(got)
                self.assertEqual(got.models, expected)

    def test_refusals_and_invalid_sources_fail_closed(self):
        self.assertIsNone(count_source_fused_in_rust(
            [[1, 2]], 2, source_preprocessor="none",
            max_inclusion_subsets=1))
        with self.assertRaises(ValueError):
            count_source_fused_in_rust(
                [[1, 2]], 2, source_preprocessor="rust_consensus",
                max_preprocess_passes=0)
        for bad in ([[3]], [[0]], [[True]], [[-4]]):
            with self.assertRaises(ValueError):
                count_source_fused_in_rust(bad, 2)
        with self.assertRaises(ValueError):
            count_signed_cnf_crc(
                [], 0, source_backend="rust_fused",
                enable_orbit_oracle=True)
        with self.assertRaises(ValueError):
            count_signed_cnf_crc([], 0, source_backend="bogus")


if __name__ == "__main__":
    unittest.main()
