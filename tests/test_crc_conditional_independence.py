"""W-CRC-010 conditioning graph certificate versus brute probability tables."""
from __future__ import annotations

import random
import unittest

from witnora_core.crc_structural_independence import (
    audit_structural_source_independence,
)
from witnora_core.crc_conditional_independence import (
    audit_conditioned_source_independence,
)


def brute_conditional_independence(source, n, left, right, separator, witness):
    smask = sum(1 << (v - 1) for v in separator)
    counts = {}
    for bits in range(1 << n):
        if bits & smask != witness & smask:
            continue
        if not all(any(bool(bits & (1 << (abs(lit) - 1))) == (lit > 0)
                       for lit in clause) for clause in source):
            continue
        a = tuple(bool(bits & (1 << (v - 1))) for v in left)
        b = tuple(bool(bits & (1 << (v - 1))) for v in right)
        counts[a, b] = counts.get((a, b), 0) + 1
    total = sum(counts.values())
    if total == 0:
        return None
    left_sums, right_sums = {}, {}
    for (a, b), value in counts.items():
        left_sums[a] = left_sums.get(a, 0) + value
        right_sums[b] = right_sums.get(b, 0) + value
    return all(total * counts.get((a, b), 0) ==
               left_sums[a] * right_sums[b]
               for a in left_sums for b in right_sums)


class TestConditionalIndependence(unittest.TestCase):
    def test_connected_xor_chain_is_only_conditionally_independent(self):
        # Equivalence 1 = 2 = 3: X1 and X3 are unconditionally
        # perfectly correlated. Given X2=1, both are fixed.
        source = [[-1, 2], [1, -2], [-2, 3], [2, -3]]
        boundary = (1, 2, 3)
        ordinary = audit_structural_source_independence(
            source, boundary, (1,), (3,), 7)
        self.assertFalse(ordinary.separated)
        got = audit_conditioned_source_independence(
            source, boundary, (1,), (3,), (2,), 7)
        self.assertTrue(got.separated_after_conditioning)
        self.assertEqual(got.separator_assignment, 2)
        self.assertTrue(brute_conditional_independence(
            source, 3, (1,), (3,), (2,), 7))

    def test_truth_of_separator_lit_can_delete_cross_clause(self):
        source = [[1, 2, 3]]
        boundary = (1, 2, 3)
        yes = audit_conditioned_source_independence(
            source, boundary, (1,), (3,), (2,), 7)
        no = audit_conditioned_source_independence(
            source, boundary, (1,), (3,), (2,), 5)
        self.assertTrue(yes.separated_after_conditioning)
        self.assertEqual(yes.residual_clauses, 0)
        self.assertFalse(no.separated_after_conditioning)
        self.assertEqual(no.residual_clauses, 1)
        self.assertTrue(brute_conditional_independence(
            source, 3, (1,), (3,), (2,), 7))
        self.assertFalse(brute_conditional_independence(
            source, 3, (1,), (3,), (2,), 5))

    def test_different_signed_separator_literals(self):
        source = [[1, 2], [-2, 3]]
        boundary = (1, 2, 3)
        for witness in (7, 5):
            with self.subTest(witness=witness):
                result = audit_conditioned_source_independence(
                    source, boundary, (1,), (3,), (2,), witness)
                self.assertTrue(result.separated_after_conditioning)
                self.assertTrue(brute_conditional_independence(
                    source, 3, (1,), (3,), (2,), witness))

    def test_witness_rejection_and_unsafe_inputs(self):
        source = [[1], [-1], [2]]
        self.assertIsNone(audit_conditioned_source_independence(
            source, (1, 2, 3), (1,), (3,), (2,), 7))
        self.assertIsNone(audit_conditioned_source_independence(
            [[1, 2, 3]], (1, 2, 3), (1,), (3,), (2,), 0))
        for bad in (
            ((1, 2, 3), (1,), (3,), (1,), 7),
            ((1, 2, 3), (1,), (3,), (4,), 7),
            ((1, 2, 3), (1,), (3,), (2,), -1),
            ((1, 2, 3), (1,), (3,), (2,), 8),
            ((1, 2, 3), (1,), (1,), (2,), 7),
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                audit_conditioned_source_independence(
                    [[1, 2, 3]], *bad)

    def test_140_planted_random_sources_have_no_false_certificates(self):
        rng = random.Random(1010)
        certified = 0
        inconclusive = 0
        for n in (5, 6):
            boundary = tuple(range(1, n + 1))
            for _ in range(70):
                source = []
                for _ in range(rng.randrange(1, 11)):
                    vs = rng.sample(boundary, rng.randrange(1, 4))
                    signed = [v if rng.randrange(2) else -v for v in vs]
                    signed[0] = vs[0]
                    source.append(signed)
                left, right, separator = (1, 2), (4, 5), (3,)
                witness = (1 << n) - 1
                result = audit_conditioned_source_independence(
                    source, boundary, left, right, separator, witness)
                self.assertIsNotNone(result)
                independent = brute_conditional_independence(
                    source, n, left, right, separator, witness)
                self.assertIsNotNone(independent)
                if result.separated_after_conditioning:
                    self.assertTrue(independent, (n, source))
                    certified += 1
                else:
                    inconclusive += 1
        self.assertGreater(certified, 0)
        self.assertGreater(inconclusive, 0)


if __name__ == "__main__":
    unittest.main()
