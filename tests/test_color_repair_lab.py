"""Check multi-start and bounded coloring repair validity."""
import unittest

from witnora_core.color_repair_lab import multistart_dsatur, bounded_recolor
from witnora_core.nonedge_matching_bound import _dsatur_greedy_coloring
from witnora_core.targeted_graph_theorems import cycle


class ColorRepairTests(unittest.TestCase):
    def test_small_families(self):
        for n, edges in [(0, ()), (1, ()), cycle(5), cycle(4),
                         (4, ((0, 1), (1, 2), (2, 3)))]:
            original = _dsatur_greedy_coloring(n, edges)
            multi = multistart_dsatur(n, edges)
            repaired = bounded_recolor(n, edges, original["coloring"])
            self.assertLessEqual(multi["bound"], original["bound"])
            self.assertLessEqual(repaired["bound"], original["bound"])
            self.assertEqual(multi, multistart_dsatur(n, edges))
            for result in (multi, repaired):
                for u, v in edges:
                    self.assertNotEqual(result["coloring"][u], result["coloring"][v])

    def test_verified_dsatur_failure(self):
        # First independently verified v21 failure.
        n = 10
        edges = ((0, 4), (0, 7), (0, 8), (0, 9), (1, 2), (1, 3),
                 (1, 4), (1, 5), (1, 9), (2, 6), (2, 9), (3, 5),
                 (3, 6), (3, 7), (4, 6), (4, 8), (5, 7), (5, 8),
                 (6, 9), (8, 9))
        original = _dsatur_greedy_coloring(n, edges)
        self.assertEqual(original["bound"], 4)
        for result in (multistart_dsatur(n, edges),
                       bounded_recolor(n, edges, original["coloring"])):
            self.assertLessEqual(result["bound"], 4)
            for u, v in edges:
                self.assertNotEqual(result["coloring"][u], result["coloring"][v])

    def test_invalid_budgets_and_coloring(self):
        with self.assertRaises(ValueError):
            bounded_recolor(2, ((0, 1),), [0, 0])
        with self.assertRaises(ValueError):
            bounded_recolor(1, (), [0], max_nodes=0)
        with self.assertRaises(ValueError):
            multistart_dsatur(1, (), starts=0)


if __name__ == "__main__":
    unittest.main()
