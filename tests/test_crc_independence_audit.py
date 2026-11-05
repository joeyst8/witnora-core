"""W-CRC-008 exact Fourier independence criterion and negative controls."""
from __future__ import annotations

from itertools import combinations
import random
import unittest

from tests.test_crc_orbit_oracle import near_complete_source
from witnora_core.crc_independence_audit import (
    audit_defect_source_independence,
)


def brute_independence(source, n, left, right):
    """Independent exhaustive count-table rank-one oracle."""
    counts = {}
    for bits in range(1 << n):
        if not all(any(bool(bits & (1 << (abs(lit) - 1))) == (lit > 0)
                       for lit in clause) for clause in source):
            continue
        a = tuple(bool(bits & (1 << (v - 1))) for v in left)
        b = tuple(bool(bits & (1 << (v - 1))) for v in right)
        counts[a, b] = counts.get((a, b), 0) + 1
    total = sum(counts.values())
    if not total:
        return None
    left_sums = {}
    right_sums = {}
    for (a, b), value in counts.items():
        left_sums[a] = left_sums.get(a, 0) + value
        right_sums[b] = right_sums.get(b, 0) + value
    return all(total * counts.get((a, b), 0) ==
               left_sums[a] * right_sums[b]
               for a in left_sums for b in right_sums)


class TestCRCIndependenceAudit(unittest.TestCase):
    def test_complete_dense_source_has_cross_group_interactions(self):
        n = 6
        boundary = tuple(range(1, n + 1))
        source = near_complete_source(
            n, 3, {v: True for v in boundary}, set())
        left, right = (1, 2, 3), (4, 5, 6)
        audit = audit_defect_source_independence(
            source, boundary, left, right)
        self.assertIsNotNone(audit)
        self.assertFalse(audit.independent)
        self.assertEqual(audit.checked_modes, 64)
        self.assertIsNotNone(audit.witness_left)
        self.assertIsNotNone(audit.witness_right)
        self.assertNotEqual(audit.discrepancy, 0)
        self.assertFalse(brute_independence(source, n, left, right))

    def test_free_group_is_provably_independent(self):
        n = 8
        active = tuple(range(1, 7))
        boundary = tuple(range(1, n + 1))
        source = near_complete_source(
            6, 3, {v: True for v in active}, set())
        left, right = (1, 2, 3), (7, 8)
        audit = audit_defect_source_independence(
            source, boundary, left, right)
        self.assertIsNotNone(audit)
        self.assertTrue(audit.independent)
        self.assertEqual(audit.checked_modes, 32)
        self.assertEqual(audit.discrepancy, 0)
        self.assertTrue(brute_independence(source, n, left, right))

    def test_random_exact_rank_one_oracle(self):
        rng = random.Random(8008)
        checked = 0
        for n in (5, 6, 7):
            universe = list(combinations(range(1, n + 1), 3))
            for _ in range(12):
                missing = set(rng.sample(universe, rng.randrange(4)))
                polarity = {v: bool(rng.randrange(2))
                            for v in range(1, n + 1)}
                source = near_complete_source(n, 3, polarity, missing)
                chosen = rng.sample(range(1, n + 1), 4)
                left = tuple(chosen[:2])
                right = tuple(chosen[2:])
                got = audit_defect_source_independence(
                    source, tuple(range(1, n + 1)), left, right)
                self.assertIsNotNone(got)
                self.assertEqual(got.independent,
                                 brute_independence(source, n, left, right))
                checked += 1
        self.assertEqual(checked, 36)

    def test_budget_and_trust_boundary(self):
        source = near_complete_source(
            6, 3, {v: True for v in range(1, 7)}, set())
        boundary = tuple(range(1, 7))
        self.assertIsNone(audit_defect_source_independence(
            source, boundary, (1, 2, 3), (4, 5, 6),
            max_modes=32))
        with self.assertRaises(ValueError):
            audit_defect_source_independence(
                source, boundary, (1, 2), (2, 3))
        with self.assertRaises(ValueError):
            audit_defect_source_independence(
                source, boundary, (1, 2), (7,))
        with self.assertRaises(ValueError):
            audit_defect_source_independence(
                source, boundary, (), (3,))
        with self.assertRaises(ValueError):
            audit_defect_source_independence(
                source, boundary, (1, 2), (3,), max_modes=0)


if __name__ == "__main__":
    unittest.main()
