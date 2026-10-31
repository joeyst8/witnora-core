"""Checks for experimental nonedge-matching coloring witnesses."""
import unittest

from witnora_core.graph_conjecture_lab import graph_metrics, graphs
from witnora_core.nonedge_matching_bound import matching_color_bound, _is_two_connected
from witnora_core.targeted_graph_theorems import cycle, mycielski_c5


class NonedgeMatchingBoundTests(unittest.TestCase):
    def test_small_known_families(self):
        samples = [
            (0, ()), (1, ()), (2, ((0, 1),)),
            (3, ((0, 1), (0, 2), (1, 2))),
            cycle(5), mycielski_c5(),
        ]
        for n, edges in samples:
            with self.subTest(n=n, edges=len(edges)):
                result = matching_color_bound(n, edges)
                chi = graph_metrics(n, edges)["chi"]
                self.assertGreaterEqual(result["bound"], chi)
                self.assertEqual(len(result["coloring"]), n)
                self.assertEqual(result, matching_color_bound(n, edges))
                for u, v in edges:
                    self.assertNotEqual(result["coloring"][u], result["coloring"][v])

    def test_exhaustive_five_vertices(self):
        for n in range(1, 6):
            for _, edges in graphs(n):
                result = matching_color_bound(n, edges)
                actual = graph_metrics(n, edges)["chi"]
                self.assertGreaterEqual(result["bound"], actual)

    def test_two_connected_classifier(self):
        self.assertTrue(_is_two_connected(3, ((0, 1), (0, 2), (1, 2))))
        self.assertTrue(_is_two_connected(*cycle(5)))
        self.assertFalse(_is_two_connected(2, ((0, 1),)))
        self.assertFalse(_is_two_connected(4, ((0, 1), (1, 2), (2, 3))))
        self.assertFalse(_is_two_connected(4, ((0, 1), (2, 3))))

    def test_bad_edges_rejected(self):
        for edges in (((0, 0),), ((1, 0),), ((0, 1), (0, 1))):
            with self.subTest(edges=edges):
                with self.assertRaises(ValueError):
                    matching_color_bound(3, edges)


if __name__ == "__main__":
    unittest.main()
