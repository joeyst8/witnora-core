"""R-006: Rust exact dyadic CNF Walsh coefficients vs Python and truth tables."""
from __future__ import annotations

from fractions import Fraction
import os
import random
import unittest

from tests.test_crc_boundary import brute_count
from witnora_core.crc_boundary import (
    _component_coefficient, _normalized_clauses, _right_components,
    count_asymmetric_boundary,
)
from witnora_core.crc_rust_walsh import query_right_walsh_in_rust


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 extension installed by dedicated Rust CI")
class TestNativeRightWalsh(unittest.TestCase):
    def test_210_random_entire_walsh_spectra_against_python_and_bruteforce(self):
        rng = random.Random(600600)
        admitted = 0
        for n in range(2, 9):
            boundary = tuple(range(1, n + 1))
            for _ in range(30):
                source = tuple(
                    tuple(rng.choice((-1, 1)) * rng.choice(boundary)
                          for _ in range(rng.randrange(4)))
                    for _ in range(rng.randrange(7))
                )
                norm = _normalized_clauses(source, boundary)
                modes = tuple(range(1 << n))
                native = query_right_walsh_in_rust(
                    norm, boundary, modes, max_subsets=256,
                    max_operations=1000000,
                )
                components = _right_components(norm, max_subsets=256)
                self.assertEqual(native is None, components is None)
                if components is None:
                    continue
                admitted += 1
                self.assertEqual(native.components, len(components))
                self.assertEqual(native.compatible_terms,
                                 sum(len(terms) for _, terms in components))
                for mode in modes:
                    expected = _component_coefficient(components, mode)
                    self.assertEqual(native.coefficients[mode], expected)
                    truth = sum(
                        (-1 if (assignment & mode).bit_count() & 1 else 1)
                        for assignment in range(1 << n)
                        if all(any(
                            bool(assignment & (1 << (abs(lit) - 1)))
                            == (lit > 0) for lit in clause)
                            for clause in source)
                    )
                    self.assertEqual(native.coefficients[mode],
                                     Fraction(truth, 1 << n))
        self.assertGreater(admitted, 150)

    def test_120_full_left_and_right_count_differentials(self):
        rng = random.Random(606120)
        counted = 0
        for _ in range(120):
            nb = rng.randint(1, 6)
            ni = rng.randint(0, 2)
            boundary = tuple(range(1, nb + 1))
            internal = tuple(range(nb + 1, nb + ni + 1))
            universe = boundary + internal
            rows = tuple(
                (sum(1 << (v - 1) for v in universe if rng.randrange(2)),
                 rng.randrange(2))
                for _ in range(rng.randrange(6))
            )
            clauses = tuple(
                tuple(rng.choice((-1, 1)) * rng.choice(boundary)
                      for _ in range(rng.randrange(4)))
                for _ in range(rng.randrange(7))
            )
            kwargs = dict(max_spectrum_terms=64, max_inclusion_subsets=256)
            python = count_asymmetric_boundary(
                rows, internal, boundary, clauses,
                coefficient_backend="python", **kwargs)
            rust = count_asymmetric_boundary(
                rows, internal, boundary, clauses,
                coefficient_backend="rust_inclusion_exclusion",
                max_rust_coefficient_operations=200000, **kwargs)
            self.assertEqual(python is None, rust is None)
            if rust is not None:
                counted += 1
                self.assertEqual(rust.models, python.models)
                self.assertEqual(rust.models,
                                 brute_count(rows, internal, boundary, clauses))
                self.assertEqual(rust.left_fourier_terms,
                                 python.left_fourier_terms)
                self.assertEqual(rust.right_violation_terms,
                                 python.right_violation_terms)
                self.assertEqual(rust.right_components,
                                 python.right_components)
                self.assertEqual(rust.coefficient_queries,
                                 python.coefficient_queries)
                self.assertEqual(rust.coefficient_backend,
                                 "inclusion_exclusion_rust")
        self.assertGreater(counted, 90)

    def test_60_variable_disconnected_global_parity_and_256_mask(self):
        boundary = tuple(range(1, 61))
        clauses = tuple(tuple(range(i, i + 3)) for i in range(1, 61, 3))
        rows = (((1 << 60) - 1, 0),)
        kwargs = dict(max_spectrum_terms=8, max_inclusion_subsets=64)
        python = count_asymmetric_boundary(
            rows, (), boundary, clauses,
            coefficient_backend="python", **kwargs)
        rust = count_asymmetric_boundary(
            rows, (), boundary, clauses,
            coefficient_backend="rust_inclusion_exclusion", **kwargs)
        self.assertEqual(python.models, (7**20 + 1) // 2)
        self.assertEqual(rust.models, python.models)
        self.assertEqual(rust.right_violation_terms, 40)
        self.assertEqual(rust.right_components, 20)
        bit = 1 << 255
        batch = query_right_walsh_in_rust(
            ((bit, 0),), (256,), (0, bit),
            max_subsets=2, max_operations=4,
        )
        self.assertEqual(batch.coefficients,
                         {0: Fraction(1, 2), bit: Fraction(-1, 2)})

    def test_explicit_fail_closed_budgets_and_malformed_input(self):
        clauses = ((1, 0),)
        self.assertIsNone(query_right_walsh_in_rust(
            clauses, (1,), (0, 1), max_subsets=1))
        self.assertIsNone(query_right_walsh_in_rust(
            clauses, (1,), (0, 1), max_subsets=2,
            max_operations=1))
        self.assertIsNone(count_asymmetric_boundary(
            (), (), (1,), ((1,),),
            coefficient_backend="rust_inclusion_exclusion",
            max_inclusion_subsets=1))
        with self.assertRaises(ValueError):
            query_right_walsh_in_rust(((1, 1),), (1,), (0,))
        with self.assertRaises(ValueError):
            query_right_walsh_in_rust(clauses, (1,), (2,))
        with self.assertRaises(ValueError):
            count_asymmetric_boundary(
                (), (), (1,), (), coefficient_backend="invalid")


if __name__ == "__main__":
    unittest.main()
