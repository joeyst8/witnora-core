"""Regression tests for two-step Kempe coloring repair."""
import unittest

from witnora_core.double_kempe_lab import double_kempe_repair
from witnora_core.nonedge_matching_bound import _dsatur_greedy_coloring
from witnora_core.targeted_graph_theorems import cycle


class DoubleKempeTests(unittest.TestCase):
    def test_valid_coloring_invariant(self):
        for n, edges in ((0, ()), (1, ()), cycle(5), cycle(4),
                         (4, ((0, 1), (1, 2), (2, 3)))):
            start = _dsatur_greedy_coloring(n, edges)
            result = double_kempe_repair(n, edges, start["coloring"],
                                         first_limit=5, second_limit=5,
                                         total_limit=20, recolor_nodes=100)
            self.assertLessEqual(result["bound"], start["bound"])
            for u, v in edges:
                self.assertNotEqual(result["coloring"][u], result["coloring"][v])

    def test_invalid_input_rejected(self):
        with self.assertRaises(ValueError):
            double_kempe_repair(2, ((0, 1),), [0, 0])
        with self.assertRaises(ValueError):
            double_kempe_repair(1, (), [0], total_limit=0)


if __name__ == "__main__":
    unittest.main()
