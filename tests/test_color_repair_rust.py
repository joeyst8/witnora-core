"""R-098: compare native bounded recoloring against the Python reference."""
import random
import unittest
from itertools import combinations

from witnora_core.color_repair_lab import bounded_recolor
from witnora_core.nonedge_matching_bound import _dsatur_greedy_coloring


class NativeColorRepairTests(unittest.TestCase):
    def test_seeded_differential(self):
        rng = random.Random(20261104)
        for trial in range(260):
            n = rng.randrange(1, 13)
            density = rng.choice((0.1, 0.3, 0.5, 0.7, 0.9))
            edges = tuple((u, v) for u, v in combinations(range(n), 2)
                          if rng.random() < density)
            initial = _dsatur_greedy_coloring(n, edges)["coloring"]
            max_changed = rng.choice((0, 1, 2, 3, 5, 12))
            max_nodes = rng.choice((1, 2, 5, 20, 100, 300))
            with self.subTest(trial=trial, n=n):
                expected = bounded_recolor(n, edges, initial,
                                           max_changed=max_changed,
                                           max_nodes=max_nodes)
                actual = bounded_recolor(n, edges, initial,
                                         max_changed=max_changed,
                                         max_nodes=max_nodes, backend="rust")
                self.assertEqual(actual, expected)

    def test_small_budget_and_invalid_input(self):
        cases = ((1, (), [0]), (3, ((0, 1), (1, 2)), [0, 1, 0]),
                 (4, ((0, 1), (0, 2), (0, 3)), [0, 1, 1, 1]))
        for n, edges, initial in cases:
            for budget in (1, 3, 10, 1000):
                self.assertEqual(
                    bounded_recolor(n, edges, initial, max_nodes=budget),
                    bounded_recolor(n, edges, initial, max_nodes=budget,
                                    backend="rust"))
        for backend in ("python", "rust"):
            with self.assertRaises(ValueError):
                bounded_recolor(2, ((0, 1),), [0, 0], backend=backend)
            with self.assertRaises(ValueError):
                bounded_recolor(1, (), [0], max_nodes=0, backend=backend)


if __name__ == "__main__":
    unittest.main()
