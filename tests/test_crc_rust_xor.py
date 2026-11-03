"""R-005: exact Rust/Python source XOR-extractor differential gates."""
from __future__ import annotations

import os
import random
import unittest

from scripts.benchmark_crc_equivalent_encodings import equivalent_encoding
from witnora_core.crc_rust_xor import extract_small_xors_in_rust
from witnora_core.crc_source import (
    _xor_cnf, extract_exact_small_xors, count_signed_cnf_crc,
)


def _models_source(source, n):
    return {
        bits for bits in range(1 << n)
        if all(any(bool(bits & (1 << (abs(lit) - 1))) == (lit > 0)
                   for lit in clause)
               for clause in source)
    }


def _models_extracted(rows, clauses, n):
    return {
        bits for bits in range(1 << n)
        if (all((bits & mask).bit_count() % 2 == rhs for mask, rhs in rows)
            and all(any(bool(bits & (1 << (abs(lit) - 1))) == (lit > 0)
                        for lit in clause)
                    for clause in clauses))
    }


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Rust extension installed in dedicated workflow")
class TestRustSmallXorExtraction(unittest.TestCase):
    def test_280_random_signed_source_exact_output_and_models(self):
        rng = random.Random(502005)
        total = 0
        for n in range(2, 9):
            for _ in range(40):
                source = [
                    [rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                     for _ in range(rng.randrange(6))]
                    for _ in range(rng.randrange(13))
                ]
                reference = extract_exact_small_xors(source, n)
                native = extract_small_xors_in_rust(source, n)
                self.assertEqual(native, reference)
                self.assertEqual(_models_source(source, n),
                                 _models_extracted(*native, n))
                total += 1
        self.assertEqual(total, 280)

    def test_exact_parity_conflicts_and_256_bit_masks(self):
        for variables in ((1,), (1, 3), (2, 3, 5), (1, 2, 3)):
            for rhs in (0, 1):
                source = list(_xor_cnf(variables, rhs))
                expected = extract_exact_small_xors(source, max(variables) + 1)
                got = extract_small_xors_in_rust(source, max(variables) + 1)
                self.assertEqual(got, expected)
                self.assertEqual(got[0],
                                 ((sum(1 << (v - 1) for v in variables), rhs),))
                self.assertEqual(got[1], ())
            conflict = list(_xor_cnf(variables, 0) | _xor_cnf(variables, 1))
            got = extract_small_xors_in_rust(conflict, max(variables) + 1)
            self.assertEqual(got, extract_exact_small_xors(
                conflict, max(variables) + 1))
            self.assertEqual({rhs for _, rhs in got[0]}, {0, 1})
        rows, residual = extract_small_xors_in_rust([(256,)], 256)
        self.assertEqual(rows, ((1 << 255, 1),))
        self.assertEqual(residual, ())

    def test_full_source_crc_counts_match_python_reference(self):
        for n in (8, 16, 32, 64):
            for family, variant in (
                ("pairwise_forcing", "base"),
                ("pairwise_forcing", "entailed_units"),
                ("pairwise_parity", "base"),
            ):
                source = equivalent_encoding(n, family, variant)
                kwargs = dict(max_inclusion_subsets=2,
                              max_coefficient_states=20000,
                              enable_orbit_oracle=True,
                              source_preprocessor="rust_adaptive")
                reference = count_signed_cnf_crc(
                    source, n, source_extractor="python", **kwargs)
                native = count_signed_cnf_crc(
                    source, n, source_extractor="rust", **kwargs)
                self.assertIsNotNone(reference)
                self.assertIsNotNone(native)
                self.assertEqual(native.models, reference.models)
                self.assertEqual(native.models, 2)
                self.assertEqual(native.extracted_affine_rows,
                                 reference.extracted_affine_rows)
                self.assertEqual(native.residual_clauses,
                                 reference.residual_clauses)

    def test_bad_inputs_and_extractor_option(self):
        with self.assertRaises(ValueError):
            extract_small_xors_in_rust([(0,)], 2)
        with self.assertRaises(ValueError):
            extract_small_xors_in_rust([(3,)], 2)
        with self.assertRaises(ValueError):
            extract_small_xors_in_rust([], 257)
        with self.assertRaises(ValueError):
            count_signed_cnf_crc([], 2, source_extractor="unknown")


if __name__ == "__main__":
    unittest.main()
