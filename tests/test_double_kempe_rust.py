"""R-100: exact-output differential tests for native two-step Kempe repair."""
import random
import unittest
from itertools import combinations

from witnora_core.double_kempe_lab import double_kempe_repair
from witnora_core.nonedge_matching_bound import _dsatur_greedy_coloring


class DoubleKempeRustTests(unittest.TestCase):
    def test_seeded_differential(self):
        rng = random.Random(20261106)
        for trial in range(170):
            n = rng.randrange(1, 12)
            density = rng.choice((0.1, 0.3, 0.5, 0.7, 0.9))
            edges = tuple((u, v) for u, v in combinations(range(n), 2)
                          if rng.random() < density)
            original = _dsatur_greedy_coloring(n, edges)["coloring"]
            options = dict(first_limit=rng.choice((1, 2, 5, 10)),
                           second_limit=rng.choice((1, 2, 5, 10)),
                           total_limit=rng.choice((1, 2, 5, 10)),
                           recolor_nodes=rng.choice((1, 3, 15, 60)))
            with self.subTest(trial=trial, n=n):
                self.assertEqual(
                    double_kempe_repair(n, edges, original, **options,
                                        backend="rust"),
                    double_kempe_repair(n, edges, original, **options))

    def test_budgets_and_invalid(self):
        for backend in ("rust", "python"):
            with self.assertRaises(ValueError):
                double_kempe_repair(1, (), [0], first_limit=0,
                                    backend=backend)
            with self.assertRaises(ValueError):
                double_kempe_repair(2, ((0, 1),), [0, 0], backend=backend)


if __name__ == "__main__":
    unittest.main()
