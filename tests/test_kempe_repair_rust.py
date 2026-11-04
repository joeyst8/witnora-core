"""R-099: compare native Kempe variants and repair against Python."""
import random
import unittest
from itertools import combinations

from witnora_core.kempe_repair_lab import kempe_swaps, kempe_repair
from witnora_core.nonedge_matching_bound import _dsatur_greedy_coloring


class NativeKempeTests(unittest.TestCase):
    def test_seeded_swap_differential(self):
        rng = random.Random(20261105)
        for trial in range(240):
            n = rng.randrange(1, 13)
            density = rng.choice((0.1, 0.3, 0.5, 0.7, 0.9))
            edges = tuple((u, v) for u, v in combinations(range(n), 2)
                          if rng.random() < density)
            initial = _dsatur_greedy_coloring(n, edges)["coloring"]
            with self.subTest(trial=trial, n=n):
                self.assertEqual(kempe_swaps(n, edges, initial, backend="rust"),
                                 kempe_swaps(n, edges, initial))
                if trial < 100:
                    self.assertEqual(
                        kempe_repair(n, edges, initial, max_swaps=4,
                                     max_nodes_each=60, backend="rust"),
                        kempe_repair(n, edges, initial, max_swaps=4,
                                     max_nodes_each=60))

    def test_invalid_coloring(self):
        for backend in ("python", "rust"):
            with self.assertRaises(ValueError):
                kempe_swaps(2, ((0, 1),), [0, 0], backend=backend)
            with self.assertRaises(ValueError):
                kempe_repair(1, (), [0], max_swaps=0, backend=backend)


if __name__ == "__main__":
    unittest.main()
