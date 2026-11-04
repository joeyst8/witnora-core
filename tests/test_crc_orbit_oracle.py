"""Independent exhaustive tests of W-CRC-004 orbit/cardinality response."""
from __future__ import annotations

import itertools
import random
import unittest
from fractions import Fraction
from math import comb

from witnora_core.crc_boundary import (
    _normalized_clauses, count_asymmetric_boundary,
)
from witnora_core.crc_orbit_oracle import query_orbit_walsh
from witnora_core.crc_source import count_signed_cnf_crc


def near_complete_source(n, rank, positive, missing):
    return tuple(
        tuple(v if positive[v] else -v for v in support)
        for support in itertools.combinations(range(1, n + 1), rank)
        if support not in missing
    )


def independent_walsh(clauses, n, mask):
    count = 0
    for bits in range(1 << n):
        if all(any(bool(bits & (1 << (abs(lit) - 1))) == (lit > 0)
                   for lit in clause) for clause in clauses):
            count += -1 if (mask & bits).bit_count() % 2 else 1
    return Fraction(count, 1 << n)


class TestCRCOrbitOracle(unittest.TestCase):
    def test_all_mode_walsh_random_polarities_and_defects(self):
        rng = random.Random(20261104)
        checked = 0
        for n in range(4, 7):
            for rank in (2, 3):
                supports = list(itertools.combinations(
                    range(1, n + 1), rank))
                for defect_count in range(rank + 1):
                    for _ in range(3):
                        polarity = {v: bool(rng.randrange(2))
                                    for v in range(1, n + 1)}
                        missing = set(rng.sample(supports, defect_count))
                        source = near_complete_source(
                            n, rank, polarity, missing)
                        normalized = _normalized_clauses(
                            source, tuple(range(1, n + 1)))
                        modes = tuple(range(1 << n))
                        result = query_orbit_walsh(
                            normalized, tuple(range(1, n + 1)), modes)
                        self.assertIsNotNone(result)
                        for mask in modes:
                            self.assertEqual(
                                result.coefficients[mask],
                                independent_walsh(source, n, mask),
                                (n, rank, defect_count, source, mask),
                            )
                        checked += 1
        self.assertGreaterEqual(checked, 50)

    def test_dense_nearly_complete_nonlin_source_count(self):
        n = 9
        missing = {(1, 2, 3), (7, 8, 9)}
        positive = {v: True for v in range(1, n + 1)}
        source = near_complete_source(n, 3, positive, missing)
        result = count_signed_cnf_crc(
            source, n, max_inclusion_subsets=1,
            enable_orbit_oracle=True,
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.models, 1 + n + comb(n, 2) + 2)
        self.assertEqual(result.coefficient_stats.coefficient_backend,
                         "orbit_cardinality")
        self.assertIsNone(count_signed_cnf_crc(
            source, n, max_inclusion_subsets=1))

    def test_dense_with_parity_left_boundary(self):
        n = 8
        positive = {v: True for v in range(1, n + 1)}
        source = near_complete_source(n, 3, positive, {(1, 2, 3)})
        boundary = tuple(range(1, n + 1))
        row = ((1 << n) - 1, 0)
        counted = count_asymmetric_boundary(
            (row,), (), boundary, source,
            max_inclusion_subsets=1, enable_orbit_oracle=True,
        )
        self.assertIsNotNone(counted)
        self.assertEqual(counted.coefficient_backend, "orbit_cardinality")
        expected = sum(
            all(any(bool(bits & (1 << (abs(lit) - 1))) == (lit > 0)
                    for lit in c) for c in source)
            and bits.bit_count() % 2 == 0
            for bits in range(1 << n)
        )
        self.assertEqual(counted.models, expected)

    def test_reject_missing_too_many_and_polarity_conflict(self):
        n, rank = 6, 3
        positive = {v: True for v in range(1, n + 1)}
        all_supports = list(itertools.combinations(
            range(1, n + 1), rank))
        source = near_complete_source(
            n, rank, positive, set(all_supports[:4]))
        self.assertIsNone(query_orbit_walsh(
            _normalized_clauses(source, tuple(range(1, n + 1))),
            tuple(range(1, n + 1)), (0,),
        ))
        full = near_complete_source(n, rank, positive, set())
        incompatible = full + ((-1, 2, 3),)
        self.assertIsNone(query_orbit_walsh(
            _normalized_clauses(incompatible, tuple(range(1, n + 1))),
            tuple(range(1, n + 1)), (0,),
        ))

    def test_free_boundary_modes_have_zero_coefficient(self):
        positive = {v: True for v in range(1, 6)}
        source = near_complete_source(5, 2, positive, set())
        boundary = tuple(range(1, 7))
        normalized = _normalized_clauses(source, boundary)
        got = query_orbit_walsh(normalized, boundary, (0, 1 << 5))
        self.assertIsNotNone(got)
        self.assertEqual(got.coefficients[1 << 5], 0)
        self.assertEqual(got.coefficients[0], Fraction(6, 32))


if __name__ == "__main__":
    unittest.main()
