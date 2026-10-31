"""Checks for the out-of-distribution coloring benchmark."""
import unittest

from witnora_core.structured_coloring_study import structured_graphs, ungated_repair
from witnora_core.nonedge_matching_bound import _dsatur_greedy_coloring


class StructuredColoringTests(unittest.TestCase):
    def test_families_and_vertex_validation(self):
        records = list(structured_graphs(seed=20261102, per_family=3))
        self.assertEqual(len(records), 15)
        self.assertEqual(len({family for family, _, _ in records}), 5)
        for family, n, edges in records:
            self.assertLessEqual(n, 16)
            self.assertEqual(edges, tuple(sorted(set(edges))))
            self.assertTrue(all(0 <= u < v < n for u, v in edges), family)

    def test_ungated_repair_never_degrades_color(self):
        records = list(structured_graphs(seed=20261102, per_family=2))
        for family, n, edges in records:
            with self.subTest(family=family, n=n):
                original = _dsatur_greedy_coloring(n, edges)
                repaired = ungated_repair(n, edges)
                self.assertLessEqual(repaired["bound"], original["bound"])
                for u, v in edges:
                    self.assertNotEqual(repaired["coloring"][u],
                                        repaired["coloring"][v])


if __name__ == "__main__":
    unittest.main()
