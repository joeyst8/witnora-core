"""Differential controls for exact Rust source-CNF polynomial cutset conditioning."""

from __future__ import annotations

from math import comb
import random
import unittest

from tests.test_factorized_violation_profile_rust import independent_profile

try:
    from witnora_ve import aux_conditioned_violation_profile_native as native_conditioned
except (ImportError, AttributeError):
    native_conditioned = None


class CutsetPolynomialAnalyticTests(unittest.TestCase):
    def test_connected_25_variable_star_formula(self):
        # For all (hub OR leaf_i) clauses, hub=true frees all leaves;
        # hub=false gives 24 independent unit clauses. Thus:
        # P(q)=2^24 + (1+q)^24.
        expected = [comb(24, k) + ((1 << 24) if k == 0 else 0)
                    for k in range(25)]
        self.assertEqual(expected[0], (1 << 24) + 1)
        self.assertEqual(sum(expected), 1 << 25)


@unittest.skipUnless(native_conditioned is not None, "native Rust wheel unavailable")
class NativeCutsetPolynomialTests(unittest.TestCase):
    def test_randomized_full_polynomial_truth_table(self):
        rng = random.Random(7112026)
        for trial in range(160):
            nvars = rng.randrange(1, 9)
            source = [
                [rng.choice((-1, 1)) * rng.randrange(1, nvars + 1)
                 for _ in range(rng.randrange(4))]
                for _ in range(rng.randrange(0, nvars + 5))
            ]
            separator = rng.sample(list(range(1, nvars + 1)),
                                   k=min(nvars, rng.randrange(3)))
            with self.subTest(trial=trial, separator=separator):
                self.assertEqual(native_conditioned(source, nvars, separator, 14, 2),
                                 independent_profile(source, nvars))

    def test_connected_star_analytic_25_variable_family(self):
        source = [[1, leaf] for leaf in range(2, 26)]
        self.assertEqual(native_conditioned(source, 25, [1], 1, 1),
                         [comb(24, k) + ((1 << 24) if k == 0 else 0)
                          for k in range(25)])

    def test_empty_clause_and_separator_does_not_double_count(self):
        self.assertEqual(native_conditioned([[], [1, -1], [2]], 2,
                                                [1], 1, 1), [0, 2, 2, 0])
        self.assertEqual(native_conditioned([], 32, [1, 2], 1, 2), [1 << 32])

    def test_reject_invalid_or_oversize_separator(self):
        for separator, max_separator in (([1, 1], 2), ([3], 1), ([1], 0)):
            with self.subTest(separator=separator):
                with self.assertRaises(ValueError):
                    native_conditioned([[1]], 2, separator, 2, max_separator)
        with self.assertRaises(ValueError):
            native_conditioned([[0]], 1, [1], 1, 1)
        with self.assertRaises(ValueError):
            native_conditioned([[1, 2, 3]], 3, [1], 1, 1)


if __name__ == "__main__":
    unittest.main()
