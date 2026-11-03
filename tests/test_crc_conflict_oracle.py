"""W-CRC-006 adversarial exact mixed-sign Fourier correction tests."""
from __future__ import annotations

from itertools import combinations
import random
import unittest

from tests.test_crc_orbit_oracle import (
    independent_walsh, near_complete_source,
)
from witnora_core.crc_boundary import (
    _normalized_clauses, count_asymmetric_boundary,
)
from witnora_core.crc_conflict_oracle import query_conflict_walsh
from witnora_core.crc_source import count_signed_cnf_crc


def add_conflict(source, support, *, replace=False):
    """Flip the sign of the first literal of an existing base clause."""
    selected = next(c for c in source
                    if tuple(sorted(abs(v) for v in c)) == support)
    changed = (-selected[0], *selected[1:])
    return ((tuple(c for c in source if c != selected))
            if replace else tuple(source)) + (changed,)


class TestCRCConflictOracle(unittest.TestCase):
    def test_random_all_mode_walsh_and_signed_polarities(self):
        rng = random.Random(600611)
        checked = 0
        for n in (6, 7):
            boundary = tuple(range(1, n + 1))
            universe = list(combinations(boundary, 3))
            for exceptions in (1, 2):
                for _ in range(5):
                    polarity = {v: bool(rng.getrandbits(1))
                                for v in boundary}
                    missing = set(rng.sample(universe, 4))
                    source = near_complete_source(
                        n, 3, polarity, missing)
                    supports = [t for t in universe if t not in missing]
                    for support in rng.sample(supports, exceptions):
                        source = add_conflict(source, support)
                    modes = tuple(range(1 << n))
                    got = query_conflict_walsh(
                        _normalized_clauses(source, boundary), boundary, modes)
                    self.assertIsNotNone(got)
                    self.assertEqual(got.exceptions, exceptions)
                    for mode in modes:
                        self.assertEqual(
                            got.coefficients[mode],
                            independent_walsh(source, n, mode),
                            (n, exceptions, source, mode))
                    checked += 1
        self.assertEqual(checked, 20)

    def test_source_replaced_sign_and_affine_left(self):
        n = 8
        boundary = tuple(range(1, n + 1))
        universe = list(combinations(boundary, 3))
        missing = set(universe[:4])
        source = near_complete_source(
            n, 3, {v: True for v in boundary}, missing)
        support = next(t for t in universe if t not in missing)
        source = add_conflict(source, support, replace=True)
        got = count_signed_cnf_crc(
            source, n, max_inclusion_subsets=2,
            enable_conflict_oracle=True)
        self.assertIsNotNone(got)
        self.assertEqual(got.coefficient_stats.coefficient_backend,
                         "conflict_walsh")
        expected_count = int(independent_walsh(source, n, 0) * (1 << n))
        self.assertEqual(got.models, expected_count)

        # Left equation requests a nonzero Fourier mode as well as 0.
        mask = (1 << n) - 1
        parity = count_asymmetric_boundary(
            ((mask, 1),), (), boundary, source,
            max_inclusion_subsets=2, enable_conflict_oracle=True)
        self.assertIsNotNone(parity)
        ref = sum(
            all(any(bool(bits & (1 << (abs(lit) - 1))) == (lit > 0)
                    for lit in clause) for clause in source)
            and bits.bit_count() % 2 == 1
            for bits in range(1 << n)
        )
        self.assertEqual(parity.models, ref)
        self.assertEqual(parity.coefficient_backend, "conflict_walsh")

    def test_free_bit_and_source_sign_adversaries(self):
        n = 7
        active = tuple(range(1, n + 1))
        missing = set(list(combinations(active, 3))[:4])
        source = near_complete_source(
            n, 3, {v: True for v in active}, missing)
        support = next(t for t in combinations(active, 3)
                       if t not in missing)
        source = add_conflict(source, support)
        boundary = tuple(range(1, 9))
        normalized = _normalized_clauses(source, boundary)
        got = query_conflict_walsh(
            normalized, boundary, (0, 1 << 7))
        self.assertIsNotNone(got)
        self.assertEqual(got.coefficients[1 << 7], 0)
        self.assertEqual(got.coefficients[0] * (1 << n),
                         independent_walsh(source, n, 0) * (1 << n))

        source3 = tuple(source)
        for support in list(combinations(active, 3)):
            if support not in missing and len(source3) < len(source) + 2:
                extra = add_conflict(source, support)[-1]
                if extra not in source3:
                    source3 += (extra,)
        self.assertEqual(len(source3), len(source) + 2)
        self.assertIsNone(query_conflict_walsh(
            _normalized_clauses(source3, boundary), boundary, (0,),
            max_exception_clauses=2))
        self.assertIsNone(query_conflict_walsh(
            normalized, boundary, (0,),
            max_exception_variables=2))
        self.assertIsNone(query_conflict_walsh(
            normalized, boundary, (0, 1),
            max_base_mode_queries=1))
        with self.assertRaises(ValueError):
            query_conflict_walsh(normalized, boundary, (1 << 9,))
        with self.assertRaises(ValueError):
            query_conflict_walsh(normalized, boundary, (0,),
                                 max_exception_clauses=-1)


if __name__ == "__main__":
    unittest.main()
