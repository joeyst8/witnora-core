"""Independent exhaustive controls for W-CRC-001's bounded exact prototype."""
import itertools
from fractions import Fraction
import random
import unittest

from witnora_core.crc_boundary import count_asymmetric_boundary


def brute_count(rows, internal, boundary, clauses):
    variables = tuple(internal) + tuple(boundary)
    total = 0
    for bits in itertools.product((0, 1), repeat=len(variables)):
        assignment = dict(zip(variables, bits))
        if any(
            (sum(assignment[v] for v in variables if mask & (1 << (v - 1))) % 2) != rhs
            for mask, rhs in rows
        ):
            continue
        if not all(
            any((assignment[abs(lit)] == (1 if lit > 0 else 0)) for lit in clause)
            for clause in clauses
        ):
            continue
        total += 1
    return total


class TestCRC001(unittest.TestCase):
    def test_parity_wide_clause(self):
        b = tuple(range(1, 13))
        parity = (1 << 12) - 1
        result = count_asymmetric_boundary(((parity, 0),), (), b, (b,))
        self.assertEqual(result.models, 2047)
        self.assertEqual(result.left_fourier_terms, 2)
        self.assertEqual(result.right_violation_terms, 2)
        self.assertEqual(result.coefficient_queries, 2)

    def test_internal_affine_projection(self):
        b = tuple(range(1, 13))
        rows = (
            ((1 << 12) | (1 << 0) | (1 << 1), 0),
            ((1 << 12) | (1 << 2) | (1 << 3), 0),
        )
        result = count_asymmetric_boundary(rows, (13, 14), b, (b,))
        self.assertEqual(result.models, 4094)
        self.assertEqual(result.internal_free_variables, 1)
        self.assertEqual(result.left_fourier_terms, 2)

    def test_contradiction(self):
        result = count_asymmetric_boundary(((3, 0), (3, 1)), (), (1, 2), ())
        self.assertEqual(result.models, 0)

    def test_duplicate_tautological_and_empty_clauses(self):
        result = count_asymmetric_boundary((), (), (1, 2), ((1, -1), (1, 2), (2, 1)))
        self.assertEqual(result.models, 3)
        zero = count_asymmetric_boundary((), (), (1, 2), ((),))
        self.assertEqual(zero.models, 0)

    def test_limits_fail_closed(self):
        self.assertIsNone(count_asymmetric_boundary(((1, 0), (2, 0)), (), (1, 2), (),
                                                     max_spectrum_terms=2))
        self.assertIsNone(count_asymmetric_boundary((), (), tuple(range(1, 15)),
                                                     tuple((1, i) for i in range(2, 15)),
                                                     max_inclusion_subsets=4096))

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            count_asymmetric_boundary((), (1,), (1,), ())
        with self.assertRaises(ValueError):
            count_asymmetric_boundary(((4, 0),), (), (1, 2), ())
        with self.assertRaises(ValueError):
            count_asymmetric_boundary((), (), (1,), ((0,),))

    def test_dense_global_parity_many_disjoint_nonlinear_clauses(self):
        # One 60-variable affine coupling crosses 20 independent
        # nonlinear OR clauses. Explicit boundary enumeration is 2**60.
        b = tuple(range(1, 61))
        clauses = tuple(tuple(range(i, i + 3)) for i in range(1, 61, 3))
        result = count_asymmetric_boundary(
            (((1 << 60) - 1, 0),), (), b, clauses,
            max_spectrum_terms=8, max_inclusion_subsets=64,
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.models, (7**20 + 1) // 2)
        self.assertEqual(result.left_fourier_terms, 2)
        self.assertEqual(result.right_violation_terms, 40)
        self.assertEqual(result.right_components, 20)

    def test_coefficient_oracle_against_direct_walsh(self):
        from witnora_core.crc_boundary import (
            _normalized_clauses, _right_violation_terms, _coefficient,
        )
        rng = random.Random(5081)
        b = tuple(range(1, 6))
        for _ in range(80):
            clauses = tuple(
                tuple(rng.choice((-1, 1)) * rng.choice(b)
                      for _ in range(rng.randrange(4)))
                for _ in range(rng.randrange(6))
            )
            terms = _right_violation_terms(_normalized_clauses(clauses, b),
                                           max_subsets=1024)
            for mode in range(1 << len(b)):
                expected = 0
                for assignment in range(1 << len(b)):
                    truth = all(
                        any(bool(assignment & (1 << (abs(lit) - 1)))
                            == (lit > 0) for lit in clause)
                        for clause in clauses
                    )
                    if truth:
                        expected += -1 if (assignment & mode).bit_count() & 1 else 1
                self.assertEqual(_coefficient(terms, mode),
                                 Fraction(expected, 1 << len(b)))

    def test_seeded_random_exhaustive(self):
        rng = random.Random(126371)
        for _ in range(400):
            nb = rng.randint(1, 6)
            ni = rng.randint(0, 3)
            b = tuple(range(1, nb + 1))
            internal = tuple(range(nb + 1, nb + ni + 1))
            all_vars = internal + b
            rows = tuple(
                (sum(1 << (v - 1) for v in all_vars if rng.randrange(2)), rng.randrange(2))
                for _ in range(rng.randrange(9))
            )
            clauses = tuple(
                tuple(rng.choice((-1, 1)) * rng.choice(b)
                      for _ in range(rng.randrange(5)))
                for _ in range(rng.randrange(9))
            )
            expected = brute_count(rows, internal, b, clauses)
            result = count_asymmetric_boundary(
                rows, internal, b, clauses, max_spectrum_terms=64,
                max_inclusion_subsets=256,
            )
            self.assertIsNotNone(result)
            self.assertEqual(result.models, expected,
                             msg=f"rows={rows} boundary={b} internal={internal} clauses={clauses}")


if __name__ == "__main__":
    unittest.main()
