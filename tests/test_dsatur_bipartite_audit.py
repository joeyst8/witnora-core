"""Bipartition certificates and DSATUR low-color property tests."""
import unittest

from witnora_core.dsatur_bipartite_audit import bipartition
from witnora_core.nonedge_matching_bound import _dsatur_greedy_coloring
from witnora_core.targeted_graph_theorems import cycle


class BipartiteAuditTests(unittest.TestCase):
    def test_valid_bipartitions(self):
        for n, edges in [(0, ()), (1, ()), (2, ((0, 1),)),
                         cycle(4), (4, ((0, 1), (2, 3)))]:
            with self.subTest(n=n, edges=edges):
                parts = bipartition(n, edges)
                self.assertIsNotNone(parts)
                self.assertEqual(len(parts), n)
                self.assertTrue(all(parts[u] != parts[v] for u, v in edges))
                expected = (2 if edges else 1) if n else 0
                self.assertEqual(_dsatur_greedy_coloring(n, edges)["bound"],
                                 expected)

    def test_odd_cycles_not_bipartite(self):
        for n, edges in [cycle(3), cycle(5)]:
            self.assertIsNone(bipartition(n, edges))


if __name__ == "__main__":
    unittest.main()
