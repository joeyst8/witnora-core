"""R-103: byte-for-byte deterministic coloring and bound comparisons."""
import random
import unittest
from itertools import combinations

from witnora_core.nonedge_matching_bound import _dsatur_greedy_coloring


class DsaturGreedyRustTests(unittest.TestCase):
    def test_seeded_graphs(self):
        rng = random.Random(20261110)
        for trial in range(440):
            n = rng.randrange(0, 20)
            density = rng.choice((0.02, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0))
            edges = tuple((u, v) for u, v in combinations(range(n), 2)
                          if rng.random() < density)
            with self.subTest(trial=trial, n=n):
                expected = _dsatur_greedy_coloring(n, edges)
                actual = _dsatur_greedy_coloring(n, edges, backend="rust")
                self.assertEqual(actual, expected)
                self.assertTrue(all(actual["coloring"][u] !=
                                    actual["coloring"][v] for u, v in edges))

    def test_invalid_backend(self):
        with self.assertRaises(ValueError):
            _dsatur_greedy_coloring(1, (), backend="unsupported")


if __name__ == "__main__":
    unittest.main()
