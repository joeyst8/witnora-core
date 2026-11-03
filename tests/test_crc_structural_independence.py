"""W-CRC-009 structural sufficient independence; exhaustive semantic controls."""
from __future__ import annotations

import random
import unittest

from tests.test_crc_independence_audit import brute_independence
from witnora_core.crc_structural_independence import (
    audit_structural_source_independence,
)


class TestCRCStructuralIndependence(unittest.TestCase):
    def test_separated_components_certify_independence(self):
        source = [[1, 2], [3, 4]]
        result = audit_structural_source_independence(
            source, (1, 2, 3, 4), (1, 2), (3, 4), 15)
        self.assertTrue(result.separated)
        self.assertTrue(result.witness_accepted)
        self.assertEqual(result.source_components, 2)
        self.assertEqual(result.clauses_checked, 2)
        self.assertTrue(brute_independence(source, 4, (1, 2), (3, 4)))

    def test_connected_graph_cannot_reject_semantic_independence(self):
        source = [[1], [2], [1, 2]]
        result = audit_structural_source_independence(
            source, (1, 2), (1,), (2,), 3)
        self.assertFalse(result.separated)
        self.assertEqual(result.source_components, 1)
        self.assertTrue(brute_independence(source, 2, (1,), (2,)))

    def test_connected_semantic_dependence(self):
        source = [[1, 2]]
        result = audit_structural_source_independence(
            source, (1, 2), (1,), (2,), 3)
        self.assertFalse(result.separated)
        self.assertFalse(brute_independence(source, 2, (1,), (2,)))

    def test_refuses_incorrect_witness_and_unsat_source(self):
        self.assertIsNone(audit_structural_source_independence(
            [[1, 2], [3, 4]], (1, 2, 3, 4), (1, 2), (3, 4), 0))
        self.assertIsNone(audit_structural_source_independence(
            [[1], [-1], [2]], (1, 2), (1,), (2,), 3))
        self.assertIsNone(audit_structural_source_independence(
            [[]], (1, 2), (1,), (2,), 3))

    def test_random_planted_witness_soundness(self):
        rng = random.Random(9009)
        positive = 0
        negative = 0
        for n in (5, 6):
            boundary = tuple(range(1, n + 1))
            for _ in range(70):
                clauses = []
                for _ in range(rng.randrange(1, 13)):
                    variables = rng.sample(boundary, rng.randrange(1, min(4, n) + 1))
                    # Every clause has at least one positive literal:
                    # the all-ones assignment is independently a source model.
                    signed = [v if rng.randrange(2) else -v for v in variables]
                    signed[0] = variables[0]
                    clauses.append(signed)
                left, right = (1, 2), (3, 4)
                result = audit_structural_source_independence(
                    clauses, boundary, left, right, (1 << n) - 1)
                self.assertIsNotNone(result)
                semantic = brute_independence(clauses, n, left, right)
                self.assertTrue(semantic is not None)
                if result.separated:
                    self.assertTrue(semantic, (n, clauses))
                    positive += 1
                else:
                    negative += 1
        self.assertGreater(positive, 0)
        self.assertGreater(negative, 0)

    def test_input_contract(self):
        base = ([[1]], (1, 2), (1,), (2,), 3)
        for bad in (
            (base[0], (1, 1), base[2], base[3], base[4]),
            (base[0], base[1], (1, 1), base[3], base[4]),
            (base[0], base[1], (1,), (1,), base[4]),
            (base[0], base[1], (3,), (2,), base[4]),
            (base[0], base[1], (1,), (2,), -1),
            (base[0], base[1], (1,), (2,), 1 << 5),
            ([[3]], base[1], (1,), (2,), 3),
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                audit_structural_source_independence(*bad)


if __name__ == "__main__":
    unittest.main()
