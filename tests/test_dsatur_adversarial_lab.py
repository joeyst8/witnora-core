"""Independent exact-coloring decision procedure regression tests."""
import unittest

from witnora_core.dsatur_adversarial_lab import exact_k_coloring, chromatic_certificate
from witnora_core.graph_conjecture_lab import graph_metrics, graphs
from witnora_core.targeted_graph_theorems import cycle


class DSATURAdversarialTests(unittest.TestCase):
    def test_known_graphs(self):
        for n, edges, chi in [
            (0, (), 0), (1, (), 1), (2, ((0, 1),), 2),
            (3, ((0, 1), (0, 2), (1, 2)), 3),
            (*cycle(5), 3), (*cycle(4), 2),
        ]:
            with self.subTest(n=n, edges=edges):
                self.assertEqual(chromatic_certificate(n, edges, n)["chi"], chi)
                self.assertIsNone(exact_k_coloring(n, edges, chi - 1))
                witness = exact_k_coloring(n, edges, chi)
                self.assertIsNotNone(witness)
                self.assertEqual(len(witness), n)
                for u, v in edges:
                    self.assertNotEqual(witness[u], witness[v])

    def test_exhaustive_small_independent_crosscheck(self):
        for n in range(1, 5):
            for _, edges in graphs(n):
                expected = graph_metrics(n, edges)["chi"]
                self.assertEqual(chromatic_certificate(n, edges, n)["chi"], expected)

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            exact_k_coloring(17, (), 2)
        with self.assertRaises(ValueError):
            exact_k_coloring(2, ((0, 0),), 2)


if __name__ == "__main__":
    unittest.main()
