"""R-007: exact native GF(2) projection and sparse Fourier checks."""
from __future__ import annotations

import os
import random
from fractions import Fraction
import unittest

from tests.test_crc_boundary import brute_count
from witnora_core.crc_boundary import (
    _project_affine, _sparse_fourier, count_asymmetric_boundary,
)
from witnora_core.crc_rust_affine import query_left_affine_in_rust
from witnora_core.crc_source import _xor_cnf, count_signed_cnf_crc


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestRustLeftAffine(unittest.TestCase):
    def test_280_seeded_projected_rows_and_all_fourier_coefficients(self):
        rng = random.Random(700700)
        for nb in (1, 2, 3, 4, 5, 6, 8):
            boundary = tuple(range(1, nb + 1))
            for _ in range(40):
                ni = rng.randrange(4)
                internal = tuple(range(nb + 1, nb + ni + 1))
                universe = boundary + internal
                rows = tuple(
                    (sum(1 << (v - 1) for v in universe if rng.randrange(2)),
                     rng.randrange(2))
                    for _ in range(rng.randrange(10))
                )
                projected, free = _project_affine(rows, internal, boundary)
                expected = _sparse_fourier(projected, free, max_terms=4096)
                native = query_left_affine_in_rust(
                    rows, internal, boundary, max_terms=4096)
                self.assertIsNotNone(native)
                self.assertEqual(native.projected_rows, projected)
                self.assertEqual(native.internal_free_variables, free)
                self.assertEqual(native.spectrum, expected)

    def test_160_random_full_count_differentials(self):
        rng = random.Random(704160)
        for _ in range(160):
            nb = rng.randrange(1, 7)
            ni = rng.randrange(4)
            boundary = tuple(range(1, nb + 1))
            internal = tuple(range(nb + 1, nb + ni + 1))
            universe = boundary + internal
            rows = tuple(
                (sum(1 << (v - 1) for v in universe if rng.randrange(2)),
                 rng.randrange(2))
                for _ in range(rng.randrange(9))
            )
            source = tuple(
                tuple(rng.choice((-1, 1)) * rng.choice(boundary)
                      for _ in range(rng.randrange(4)))
                for _ in range(rng.randrange(7))
            )
            kwargs = dict(max_spectrum_terms=256,
                          max_inclusion_subsets=256)
            reference = count_asymmetric_boundary(
                rows, internal, boundary, source, left_backend="python",
                **kwargs)
            native = count_asymmetric_boundary(
                rows, internal, boundary, source, left_backend="rust",
                **kwargs)
            self.assertEqual(reference is None, native is None)
            if native is not None:
                self.assertEqual(native.models, reference.models)
                self.assertEqual(native.models,
                                 brute_count(rows, internal, boundary, source))
                self.assertEqual(native.left_fourier_terms,
                                 reference.left_fourier_terms)
                self.assertEqual(native.internal_free_variables,
                                 reference.internal_free_variables)

    def test_all_four_native_source_stages_against_python_and_analytic(self):
        for groups in (4, 8, 20):
            n = 3 * groups
            for xor_blocks in (0, 1, 2, 3):
                source = []
                for group in range(groups):
                    triple = tuple(range(3 * group + 1, 3 * group + 4))
                    source.append(triple)
                    if group < xor_blocks:
                        source.extend(_xor_cnf(triple, 0))
                expected = 3**xor_blocks * 7**(groups - xor_blocks)
                common = dict(max_spectrum_terms=128,
                              max_inclusion_subsets=512,
                              max_coefficient_states=200000)
                python = count_signed_cnf_crc(
                    source, n, source_preprocessor="none",
                    source_extractor="python", left_backend="python",
                    coefficient_backend="python", **common)
                rust = count_signed_cnf_crc(
                    source, n, source_preprocessor="rust_adaptive",
                    source_extractor="rust", left_backend="rust",
                    coefficient_backend="rust_inclusion_exclusion",
                    **common)
                self.assertIsNotNone(python)
                self.assertIsNotNone(rust)
                self.assertEqual(python.models, expected)
                self.assertEqual(rust.models, expected)
                self.assertEqual(rust.coefficient_stats.coefficient_backend,
                                 "inclusion_exclusion_rust")

    def test_malformed_sparse_256_bit_and_fail_closed_limits(self):
        bit = 1 << 255
        got = query_left_affine_in_rust(((bit, 1),), (), (256,), max_terms=2)
        self.assertEqual(got.projected_rows, ((bit, 1),))
        self.assertEqual(got.spectrum, {0: Fraction(1, 2), bit: Fraction(-1, 2)})
        self.assertIsNone(query_left_affine_in_rust(
            ((1, 0), (2, 0)), (), (1, 2), max_terms=2))
        self.assertEqual(query_left_affine_in_rust(
            ((0, 1),), (), (1,), max_terms=1).spectrum, {})
        with self.assertRaises(ValueError):
            query_left_affine_in_rust(((4, 0),), (), (1, 2))
        with self.assertRaises(ValueError):
            query_left_affine_in_rust((), (1,), (1,))
        with self.assertRaises(ValueError):
            count_asymmetric_boundary((), (), (1,), (),
                                      left_backend="unknown")


if __name__ == "__main__":
    unittest.main()
