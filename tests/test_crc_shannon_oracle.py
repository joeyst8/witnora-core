"""Exact Shannon-coefficient oracle controls independent of the CRC front end."""
from fractions import Fraction
import random
import unittest

from witnora_core.crc_shannon_oracle import query_walsh_coefficients


def direct_walsh(clauses, boundary, mode):
    total = 0
    for bits in range(1 << len(boundary)):
        assignment = {v: bool(bits & (1 << i)) for i, v in enumerate(boundary)}
        good = all(any(assignment[abs(lit)] == (lit > 0) for lit in clause)
                   for clause in clauses)
        if good:
            sign_parity = sum(int(assignment[v]) for v in boundary
                              if mode & (1 << (v - 1))) % 2
            total += (-1 if sign_parity else 1)
    return Fraction(total, 1 << len(boundary))


def violations(clauses):
    result = []
    for clause in clauses:
        zeros = ones = 0
        for lit in clause:
            if lit > 0:
                zeros |= 1 << (lit - 1)
            else:
                ones |= 1 << (-lit - 1)
        result.append((zeros, ones))
    return tuple(result)


class TestShannonWalsh(unittest.TestCase):
    def test_complete_coefficients_for_overlapping_cnf(self):
        rng = random.Random(100122)
        for _ in range(120):
            n = rng.randint(1, 7)
            boundary = tuple(range(1, n + 1))
            clauses = tuple(
                tuple(rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                      for _ in range(rng.randrange(1, 5)))
                for _ in range(rng.randrange(1, 15))
            )
            # Avoid tautologies in this direct normalized-oracle test.
            clauses = tuple(c for c in clauses if not set(c).intersection(-x for x in c))
            modes = tuple(range(1 << n))
            result = query_walsh_coefficients(
                violations(clauses), boundary, modes, max_states=100_000,
            )
            self.assertIsNotNone(result)
            for mode in modes:
                self.assertEqual(result.coefficients[mode],
                                 direct_walsh(clauses, boundary, mode))

    def test_empty_and_free(self):
        boundary = (1, 2, 3)
        result = query_walsh_coefficients((), boundary, (0, 1, 7), max_states=50)
        self.assertEqual(result.coefficients, {0: Fraction(1), 1: Fraction(0),
                                               7: Fraction(0)})
        empty = query_walsh_coefficients(None, boundary, (0, 7), max_states=50)
        self.assertEqual(empty.coefficients, {0: Fraction(), 7: Fraction()})

    def test_budget_fails_closed(self):
        clauses = tuple((1, v) for v in range(2, 16))
        self.assertIsNone(query_walsh_coefficients(
            violations(clauses), tuple(range(1, 16)), (0,),
            max_states=1,
        ))
