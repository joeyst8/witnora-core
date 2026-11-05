"""Source-literal truth-table controls for Rust Fourier violation parity projection."""

from __future__ import annotations

from math import comb
import random
import unittest

from tests.test_factorized_violation_profile_rust import independent_profile

try:
    from witnora_ve import aux_fourier_parity_violation_profile_native as native_fourier
except (ImportError, AttributeError):
    native_fourier = None


def independent_filtered_profile(source: list[list[int]], nvars: int,
                                 rows: list[list[int]], rhs: list[bool]) -> list[int]:
    coefficients = [0] * (len(source) + 1)
    for assignment in range(1 << nvars):
        violated = [not any(
            bool(assignment & (1 << (abs(lit) - 1))) == (lit > 0)
            for lit in clause) for clause in source]
        if all(sum(violated[j] for j in row) % 2 == int(target)
               for row, target in zip(rows, rhs)):
            coefficients[sum(violated)] += 1
    return coefficients


def exhaustive_character_projection(source: list[list[int]], nvars: int,
                                    rows: list[list[int]], rhs: list[bool]) -> list[int]:
    """Independent character-sum formula, without component factorization."""
    modes = 1 << len(rows)
    target = sum((1 << j) for j, bit in enumerate(rhs) if bit)
    transformed = [[0] * modes for _ in range(len(source) + 1)]
    for assignment in range(1 << nvars):
        violated = [not any(
            bool(assignment & (1 << (abs(lit) - 1))) == (lit > 0)
            for lit in clause) for clause in source]
        syndrome = sum((1 << j) for j, row in enumerate(rows)
                       if sum(violated[k] for k in row) % 2)
        degree = sum(violated)
        for frequency in range(modes):
            transformed[degree][frequency] += (
                -1 if (frequency & syndrome).bit_count() % 2 else 1)
    numerators = [sum(coefficient * (-1 if (frequency & target).bit_count() % 2 else 1)
                      for frequency, coefficient in enumerate(degree_row))
                  for degree_row in transformed]
    if any(value % modes for value in numerators):
        raise ArithmeticError("character projection was not integral")
    return [value // modes for value in numerators]


class CharacterProjectionIdentityTests(unittest.TestCase):
    def test_96_random_character_identities_vs_direct_parity_filter(self):
        rng = random.Random(8122026)
        for trial in range(96):
            nvars = rng.randrange(1, 8)
            source = [[rng.choice((-1, 1)) * rng.randrange(1, nvars + 1)
                       for _ in range(rng.randrange(4))]
                      for _ in range(rng.randrange(1, 10))]
            rows = [[rng.randrange(len(source)) for _ in range(rng.randrange(4))]
                    for _ in range(rng.randrange(4))]
            rhs = [bool(rng.getrandbits(1)) for _ in rows]
            with self.subTest(trial=trial):
                self.assertEqual(exhaustive_character_projection(source, nvars, rows, rhs),
                                 independent_filtered_profile(source, nvars, rows, rhs))

    def test_analytic_even_odd_parity_of_disconnected_binary_clauses(self):
        # For 12 disjoint (x OR y), P(q)=(3+q)^12 and
        # Q_even/odd(q)=((3+q)^12 +/- (3-q)^12)/2.
        even = [comb(12, k) * 3 ** (12 - k) if k % 2 == 0 else 0
                for k in range(13)]
        odd = [comb(12, k) * 3 ** (12 - k) if k % 2 == 1 else 0
               for k in range(13)]
        self.assertEqual(even[0], 3 ** 12)
        self.assertEqual(odd[0], 0)
        self.assertEqual(sum(even) + sum(odd), 1 << 24)
        self.assertEqual(sum(even), ((1 << 24) + (1 << 12)) // 2)

    def test_zero_energy_is_never_filtered_by_homogeneous_parity(self):
        source = [[1, 2], [-1, 3], [2, -3]]
        original = independent_profile(source, 3)
        for rows in ([[]], [[0, 1, 2]], [[0], [1, 2]]):
            with self.subTest(rows=rows):
                self.assertEqual(independent_filtered_profile(source, 3, rows,
                                                              [False] * len(rows))[0],
                                 original[0])
                if rows:
                    self.assertEqual(independent_filtered_profile(source, 3, rows,
                                                                  [True] + [False] * (len(rows)-1))[0],
                                     0)


@unittest.skipUnless(native_fourier is not None, "native Rust wheel unavailable")
class NativeFourierParityTests(unittest.TestCase):
    def test_240_seeded_random_source_syndromes(self):
        rng = random.Random(8112026)
        for trial in range(240):
            nvars = rng.randrange(1, 9)
            source = [[rng.choice((-1, 1)) * rng.randrange(1, nvars + 1)
                       for _ in range(rng.randrange(4))]
                      for _ in range(rng.randrange(0, nvars + 5))]
            rows = [[rng.randrange(len(source)) for _ in range(rng.randrange(4))]
                    if source else [] for _ in range(rng.randrange(4))]
            rhs = [bool(rng.getrandbits(1)) for _ in rows]
            with self.subTest(trial=trial):
                self.assertEqual(native_fourier(source, nvars, rows, rhs, 14),
                                 independent_filtered_profile(source, nvars, rows, rhs))

    def test_24_variable_coupled_parity_analytic_family(self):
        source = [[2 * j + 1, 2 * j + 2] for j in range(12)]
        row = [list(range(12))]
        even = [comb(12, k) * 3 ** (12 - k) if k % 2 == 0 else 0
                for k in range(13)]
        odd = [comb(12, k) * 3 ** (12 - k) if k % 2 == 1 else 0
               for k in range(13)]
        self.assertEqual(native_fourier(source, 24, row, [False], 2), even)
        self.assertEqual(native_fourier(source, 24, row, [True], 2), odd)

    def test_empty_clause_redundancy_and_parity_free_equivalence(self):
        source = [[], [1, -1], [2], [-2]]
        rows = [[0, 0], [2, 3], [0, 2, 2]]
        for mask in range(8):
            rhs = [bool(mask & (1 << j)) for j in range(3)]
            self.assertEqual(native_fourier(source, 2, rows, rhs, 2),
                             independent_filtered_profile(source, 2, rows, rhs))
        self.assertEqual(native_fourier(source, 2, [], [], 2),
                         independent_profile(source, 2))

    def test_fails_closed_on_invalid_rows_and_components(self):
        with self.assertRaises(ValueError):
            native_fourier([[1]], 1, [[1]], [False], 1)
        with self.assertRaises(ValueError):
            native_fourier([[1]], 1, [[0]], [], 1)
        with self.assertRaises(ValueError):
            native_fourier([[0]], 1, [], [], 1)
        with self.assertRaises(ValueError):
            native_fourier([[1, 2]], 2, [], [], 1)


if __name__ == "__main__":
    unittest.main()
