"""R-089: compiled Rust differential tests, never a novelty assertion."""
import random
import unittest

from witnora_core.graph_conjecture_lab import discover_conjectures, graph_metrics

try:
    from witnora_ve import graph_conjecture_metrics_native, graph_conjecture_run_native
except ImportError:
    graph_conjecture_metrics_native = graph_conjecture_run_native = None


@unittest.skipUnless(graph_conjecture_metrics_native is not None, "native Rust wheel unavailable")
class GraphConjectureRustTests(unittest.TestCase):
    def test_graph_metrics_500_seeded(self):
        rng = random.Random(89089)
        for index in range(500):
            n = rng.randrange(12 if index < 24 else 9)
            edges = tuple((u, v) for u in range(n) for v in range(u + 1, n)
                          if rng.randrange(2))
            with self.subTest(n=n, edges=edges):
                self.assertEqual(graph_metrics(n, edges), graph_metrics(n, edges, backend="rust"))

    def test_reports(self):
        for per_size, seeds in ((5, (8123,)), (15, (9341, 8123)),
                                (60, (8123, 9341))):
            with self.subTest(per_size=per_size):
                kwargs = dict(holdout_per_size=per_size, holdout_seeds=seeds)
                self.assertEqual(discover_conjectures(**kwargs),
                                 discover_conjectures(**kwargs, backend="rust"))

    def test_invalid_graphs(self):
        for n, edges in ((12, []), (3, [(1, 1)]), (3, [(2, 0)]),
                         (2, [(0, 2)])):
            with self.assertRaises(ValueError):
                graph_metrics(n, tuple(edges), backend="rust")


if __name__ == "__main__":
    unittest.main()
