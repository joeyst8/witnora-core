"""Independent source-CNF truth-table oracle for Rust partition-polynomial factorization."""

from __future__ import annotations

from math import comb
import random
import unittest

try:
    from witnora_ve import aux_factorized_violation_profile_native as native_profile
except (ImportError, AttributeError):
    native_profile = None


def independent_profile(source: list[list[int]], nvars: int) -> list[int]:
    out = [0] * (len(source) + 1)
    for assignment in range(1 << nvars):
        violations = 0
        for clause in source:
            if not any(bool(assignment & (1 << (abs(lit) - 1))) == (lit > 0)
                       for lit in clause):
                violations += 1
        out[violations] += 1
    return out


class SourceViolationPolynomialTests(unittest.TestCase):
    def test_analytic_independent_binary_clause_family(self):
        # Each (u OR v) block has three zero-energy assignments and one
        # assignment with one violated clause. Z(q) = (3 + q)^12.
        expected = [comb(12, k) * 3 ** (12 - k) for k in range(13)]
        self.assertEqual(sum(expected), 1 << 24)
        self.assertEqual(expected[0], 3 ** 12)


@unittest.skipUnless(native_profile is not None, "native Rust wheel unavailable")
class RustPartitionFactorizationTests(unittest.TestCase):
    def test_seeded_source_truth_table_parity(self):
        rng = random.Random(6132026)
        for trial in range(240):
            n = rng.randrange(1, 9)
            source = [[rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                       for _ in range(rng.randrange(4))]
                      for _ in range(rng.randrange(0, n + 5))]
            with self.subTest(trial=trial):
                self.assertEqual(native_profile(source, n, 14),
                                 independent_profile(source, n))

    def test_24_variable_analytic_composition(self):
        source = [[2 * j + 1, 2 * j + 2] for j in range(12)]
        self.assertEqual(native_profile(source, 24, 2),
                         [comb(12, k) * 3 ** (12 - k) for k in range(13)])

    def test_fail_closed_caps_and_malformed_literal(self):
        with self.assertRaises(ValueError):
            native_profile([[1, 2]], 2, 1)
        with self.assertRaises(ValueError):
            native_profile([[3]], 2, 2)
        with self.assertRaises(ValueError):
            native_profile([[0]], 2, 2)

    def test_empty_clauses_and_free_variables(self):
        self.assertEqual(native_profile([[], []], 0, 2), [0, 0, 1])
        self.assertEqual(native_profile([[], [1, -1], [2]], 2, 2),
                         [0, 2, 2, 0])
        self.assertEqual(native_profile([], 32, 1), [1 << 32])


if __name__ == "__main__":
    unittest.main()
