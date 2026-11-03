"""W-CRC-011 minimum separator discovery against brute vertex cuts."""
from __future__ import annotations

from itertools import combinations
import random
import unittest

from tests.test_crc_conditional_independence import (
    brute_conditional_independence,
)
from witnora_core.crc_separator_discovery import discover_source_separator


def brute_min_separator(source, n, left, right):
    graph = {v: set() for v in range(1, n + 1)}
    for clause in source:
        scope = set(abs(lit) for lit in clause)
        for u, v in combinations(sorted(scope), 2):
            graph[u].add(v)
            graph[v].add(u)
    possible = sorted(set(graph) - set(left) - set(right))
    for size in range(len(possible) + 1):
        for removed in combinations(possible, size):
            seen = set(left)
            pending = list(left)
            while pending:
                v = pending.pop()
                for u in graph[v]:
                    if u not in seen and u not in removed:
                        seen.add(u)
                        pending.append(u)
            if not seen.intersection(right):
                return size
    return None


class TestSeparatorDiscovery(unittest.TestCase):
    def test_star_one_variable_cut(self):
        n, hub = 16, 16
        clauses = [[v, hub] for v in range(1, hub)]
        result = discover_source_separator(
            clauses, tuple(range(1, n + 1)),
            (1, 2), (13, 14), (1 << n) - 1)
        self.assertIsNotNone(result)
        self.assertEqual(result.minimum_size, 1)
        self.assertEqual(result.separator, (hub,))
        self.assertTrue(result.conditional_certificate.separated_after_conditioning)

    def test_two_vertex_disjoint_paths_require_two_hubs(self):
        clauses = [[1, 5], [5, 3], [1, 6], [6, 3]]
        result = discover_source_separator(
            clauses, (1, 2, 3, 4, 5, 6),
            (1,), (3,), 63, max_separator_size=2)
        self.assertEqual(result.separator, (5, 6))
        self.assertEqual(result.minimum_size, 2)
        self.assertIsNone(discover_source_separator(
            clauses, (1, 2, 3, 4, 5, 6),
            (1,), (3,), 63, max_separator_size=1))

    def test_direct_group_edge_cannot_be_cut(self):
        self.assertIsNone(discover_source_separator(
            [[1, 2]], (1, 2, 3), (1,), (2,), 7,
            max_separator_size=2))

    def test_direct_edge_rejected_even_if_cut_budget_exceeds_n(self):
        self.assertIsNone(discover_source_separator(
            [[1, 2]], (1, 2), (1,), (2,), 3,
            max_separator_size=100))

    def test_disconnected_zero_cut(self):
        result = discover_source_separator(
            [[1, 3], [2, 4]], (1, 2, 3, 4),
            (1,), (2,), 15, max_separator_size=0)
        self.assertEqual(result.separator, ())
        self.assertEqual(result.minimum_size, 0)

    def test_witness_and_resource_boundaries(self):
        self.assertIsNone(discover_source_separator(
            [[1], [-1]], (1, 2), (1,), (2,), 3))
        self.assertIsNone(discover_source_separator(
            [[1, 2]], (1, 2, 3), (1,), (3,), 0))
        self.assertIsNone(discover_source_separator(
            [[1, 3], [3, 2]], (1, 2, 3), (1,), (2,), 7,
            max_primal_edges=1))
        for keyword in ({"max_separator_size": -1}, {"max_primal_edges": -1}):
            with self.assertRaises(ValueError):
                discover_source_separator(
                    [[1, 3]], (1, 2, 3), (1,), (2,), 7, **keyword)

    def test_seeded_random_min_cut_and_conditional_probability(self):
        rng = random.Random(11011)
        admitted = 0
        refused = 0
        for _ in range(100):
            n = 6
            source = []
            for _ in range(rng.randrange(0, 10)):
                vs = rng.sample(range(1, n + 1), rng.randrange(1, 4))
                source.append(vs)  # all-ones source model
            expected = brute_min_separator(source, n, (1,), (2,))
            result = discover_source_separator(
                source, tuple(range(1, n + 1)), (1,), (2,),
                (1 << n) - 1, max_separator_size=2)
            if expected is None or expected > 2:
                self.assertIsNone(result)
                refused += 1
                continue
            self.assertIsNotNone(result)
            self.assertEqual(result.minimum_size, expected)
            self.assertEqual(len(result.separator), expected)
            self.assertTrue(result.conditional_certificate.separated_after_conditioning)
            self.assertTrue(brute_conditional_independence(
                source, n, (1,), (2,), result.separator, 63))
            admitted += 1
        self.assertGreater(admitted, 0)
        self.assertGreater(refused, 0)


if __name__ == "__main__":
    unittest.main()
