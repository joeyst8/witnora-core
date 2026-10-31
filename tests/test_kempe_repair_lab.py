"""Soundness checks for graph two-color Kempe component swaps."""
import unittest

from witnora_core.kempe_repair_lab import kempe_swaps, kempe_repair
from witnora_core.nonedge_matching_bound import _dsatur_greedy_coloring
from witnora_core.targeted_graph_theorems import cycle


class KempeRepairTests(unittest.TestCase):
    def test_each_swap_preserves_proper_coloring(self):
        samples = [(0, ()), (1, ()), cycle(4), cycle(5),
                   (4, ((0, 1), (1, 2), (2, 3)))]
        for n, edges in samples:
            initial = _dsatur_greedy_coloring(n, edges)["coloring"]
            for variant in kempe_swaps(n, edges, initial):
                self.assertEqual(len(variant["coloring"]), n)
                self.assertLessEqual(len(set(variant["coloring"])), len(set(initial)))
                for u, v in edges:
                    self.assertNotEqual(variant["coloring"][u], variant["coloring"][v])

    def test_kempe_repair_checked_witness(self):
        n = 10
        edges = ((0, 4), (0, 7), (0, 8), (0, 9), (1, 2), (1, 3),
                 (1, 4), (1, 5), (1, 9), (2, 6), (2, 9), (3, 5),
                 (3, 6), (3, 7), (4, 6), (4, 8), (5, 7), (5, 8),
                 (6, 9), (8, 9))
        initial = _dsatur_greedy_coloring(n, edges)["coloring"]
        candidate = kempe_repair(n, edges, initial)
        self.assertLessEqual(candidate["bound"], 4)
        for u, v in edges:
            self.assertNotEqual(candidate["coloring"][u], candidate["coloring"][v])

    def test_invalid_initial_rejected(self):
        with self.assertRaises(ValueError):
            kempe_swaps(2, ((0, 1),), [0, 0])
        with self.assertRaises(ValueError):
            kempe_repair(1, (), [0], max_swaps=0)


if __name__ == "__main__":
    unittest.main()
