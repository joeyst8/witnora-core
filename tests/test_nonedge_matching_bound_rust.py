"""R-105: compare full constructive cover/nonedge-matching witnesses."""
import random
import unittest
from itertools import combinations

from witnora_core.nonedge_matching_bound import matching_color_bound


class MatchingColorBoundRustTests(unittest.TestCase):
    def test_seeded_exact_witnesses(self):
        rng = random.Random(20261112)
        for trial in range(150):
            n = rng.randrange(0, 9) if trial < 135 else rng.randrange(9, 12)
            p = rng.choice((0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0))
            edges = tuple((u, v) for u, v in combinations(range(n), 2)
                          if rng.random() < p)
            with self.subTest(trial=trial, n=n):
                self.assertEqual(matching_color_bound(n, edges, backend="rust"),
                                 matching_color_bound(n, edges))

    def test_invalid_inputs(self):
        for backend in ("python", "rust"):
            with self.assertRaises(ValueError):
                matching_color_bound(12, (), backend=backend)
            with self.assertRaises(ValueError):
                matching_color_bound(2, ((0, 1), (0, 1)), backend=backend)


if __name__ == "__main__":
    unittest.main()
