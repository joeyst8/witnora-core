"""Independent W-CRC-005 defect-hypergraph coefficient and source tests."""
from __future__ import annotations

from itertools import combinations
from math import comb
import random
import unittest

from scripts.benchmark_crc_symmetry_stress import DISPERSED, TETRAHEDRON
from tests.test_crc_orbit_oracle import (
    independent_walsh, near_complete_source,
)
from witnora_core.crc_boundary import (
    _normalized_clauses, count_asymmetric_boundary,
)
from witnora_core.crc_defect_oracle import query_defect_walsh
from witnora_core.crc_source import count_signed_cnf_crc


def brute_models(clauses, n):
    return (1 << n) * independent_walsh(clauses, n, 0)


class TestCRCDefectOracle(unittest.TestCase):
    def test_random_full_walsh_spectrum_against_independent_oracle(self):
        rng = random.Random(55026)
        checked = 0
        for n in (5, 6, 7):
            supports = list(combinations(range(1, n + 1), 3))
            for defects in (4, 5, 6):
                for _ in range(3):
                    missing = set(rng.sample(supports, defects))
                    polarity = {v: bool(rng.getrandbits(1))
                                for v in range(1, n + 1)}
                    source = near_complete_source(n, 3, polarity, missing)
                    boundary = tuple(range(1, n + 1))
                    clauses = _normalized_clauses(source, boundary)
                    modes = tuple(range(1 << n))
                    got = query_defect_walsh(clauses, boundary, modes)
                    self.assertIsNotNone(got)
                    self.assertEqual(got.missing_clauses, defects)
                    for mode in modes:
                        self.assertEqual(got.coefficients[mode],
                                         independent_walsh(source, n, mode),
                                         (n, defects, source, mode))
                    checked += 1
        self.assertEqual(checked, 27)

    def test_four_missing_triples_have_different_exact_counts(self):
        n = 8
        boundary = tuple(range(1, n + 1))
        for missing, expected in ((DISPERSED, 41), (TETRAHEDRON, 42)):
            source = near_complete_source(
                n, 3, {v: True for v in boundary}, set(missing))
            modes = (0, 0b1111, 0b10001)
            got = query_defect_walsh(
                _normalized_clauses(source, boundary), boundary, modes)
            self.assertIsNotNone(got)
            self.assertEqual(got.coefficients[0] * (1 << n), expected)
            self.assertEqual(got.high_weight_flip_sets,
                             5 if missing == TETRAHEDRON else 4)
            for mode in modes:
                self.assertEqual(got.coefficients[mode],
                                 independent_walsh(source, n, mode))
            source_count = count_signed_cnf_crc(
                source, n, max_inclusion_subsets=2,
                enable_defect_oracle=True)
            self.assertIsNotNone(source_count)
            self.assertEqual(source_count.models, expected)
            self.assertEqual(source_count.coefficient_stats.coefficient_backend,
                             "defect_hypergraph")
            self.assertIsNone(count_signed_cnf_crc(
                source, n, max_inclusion_subsets=2))

    def test_rank_two_triangle_missing_edges_support_triple_flip(self):
        n = 6
        missing = {(1, 2), (1, 3), (2, 3)}
        source = near_complete_source(
            n, 2, {v: True for v in range(1, n + 1)}, missing)
        boundary = tuple(range(1, n + 1))
        modes = tuple(range(1 << n))
        got = query_defect_walsh(
            _normalized_clauses(source, boundary), boundary, modes)
        self.assertIsNotNone(got)
        self.assertEqual(got.high_weight_flip_sets, 4)
        self.assertEqual(got.coefficients[0] * (1 << n),
                         1 + n + len(missing) + 1)
        for mode in modes:
            self.assertEqual(got.coefficients[mode],
                             independent_walsh(source, n, mode))

    def test_affine_left_and_free_boundary_coefficients(self):
        n = 8
        source = near_complete_source(
            n, 3, {v: True for v in range(1, n + 1)}, set(TETRAHEDRON))
        boundary = tuple(range(1, n + 1))
        parity_row = ((1 << n) - 1, 1)
        got = count_asymmetric_boundary(
            (parity_row,), (), boundary, source,
            max_inclusion_subsets=2, enable_defect_oracle=True)
        self.assertIsNotNone(got)
        expected = 0
        for bits in range(1 << n):
            if (bits.bit_count() % 2 == 1 and
                all(any(bool(bits & (1 << (abs(lit) - 1))) ==
                        (lit > 0) for lit in clause) for clause in source)):
                expected += 1
        self.assertEqual(got.models, expected)
        self.assertEqual(got.coefficient_backend, "defect_hypergraph")

        active = tuple(range(1, 8))
        source7 = near_complete_source(
            7, 3, {v: True for v in active}, set(TETRAHEDRON))
        modes = (0, 1 << 7)
        extra = query_defect_walsh(
            _normalized_clauses(source7, boundary), boundary, modes)
        self.assertIsNotNone(extra)
        self.assertEqual(extra.coefficients[1 << 7], 0)
        self.assertEqual(extra.coefficients[0] * (1 << 7),
                         1 + 7 + comb(7, 2) + 4 + 1)

    def test_fails_closed_on_polarity_and_limits(self):
        n = 7
        source = near_complete_source(
            n, 3, {v: True for v in range(1, n + 1)}, set(TETRAHEDRON))
        boundary = tuple(range(1, n + 1))
        normalized = _normalized_clauses(source, boundary)
        self.assertIsNone(query_defect_walsh(
            normalized, boundary, (0,), max_missing=3))
        self.assertIsNone(query_defect_walsh(
            normalized, boundary, (0,), max_defect_variables=3))
        self.assertIsNone(query_defect_walsh(
            normalized, boundary, (0,), max_subset_checks=2))
        conflict = source + ((-1, 2, 3),)
        self.assertIsNone(query_defect_walsh(
            _normalized_clauses(conflict, boundary), boundary, (0,)))
        with self.assertRaises(ValueError):
            query_defect_walsh(normalized, boundary, (1 << 8,))
        with self.assertRaises(ValueError):
            query_defect_walsh(normalized, boundary, (0,),
                               max_missing=-1)


if __name__ == "__main__":
    unittest.main()
