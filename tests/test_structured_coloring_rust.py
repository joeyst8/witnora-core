"""R-101: native clique witness and end-to-end ungated repair comparisons."""
import random
import unittest
from itertools import combinations

from witnora_core.structured_coloring_study import (
    greedy_clique_lower_bound, ungated_repair,
)


class StructuredColoringRustTests(unittest.TestCase):
    def test_seeded_clique_differential(self):
        rng = random.Random(20261107)
        for trial in range(320):
            n = rng.randrange(0, 18)
            p = rng.choice((0.05, 0.20, 0.45, 0.70, 0.95))
            edges = tuple((u, v) for u, v in combinations(range(n), 2)
                          if rng.random() < p)
            with self.subTest(trial=trial, n=n):
                self.assertEqual(greedy_clique_lower_bound(n, edges,
                                                           backend="rust"),
                                 greedy_clique_lower_bound(n, edges))

    def test_ungated_repair_differential(self):
        rng = random.Random(20261108)
        for trial in range(64):
            n = rng.randrange(2, 11)
            p = rng.choice((0.1, 0.3, 0.5, 0.7, 0.9))
            edges = tuple((u, v) for u, v in combinations(range(n), 2)
                          if rng.random() < p)
            with self.subTest(trial=trial, n=n):
                self.assertEqual(ungated_repair(n, edges, backend="rust"),
                                 ungated_repair(n, edges))


if __name__ == "__main__":
    unittest.main()
