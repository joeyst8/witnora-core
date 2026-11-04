"""R-063: independently compare native BFS partitions to Python."""
import os
import random
import unittest
from itertools import combinations

from witnora_core.dsatur_bipartite_audit import bipartition, bipartition_rust


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in Rust CI")
class BipartiteAuditRustTests(unittest.TestCase):
    def test_every_simple_graph_up_to_five_vertices(self):
        for n in range(6):
            pairs = list(combinations(range(n), 2))
            for mask in range(1 << len(pairs)):
                edges = tuple(pair for i, pair in enumerate(pairs)
                              if mask & (1 << i))
                self.assertEqual(bipartition_rust(n, edges),
                                 bipartition(n, edges))

    def test_random_disconnected_and_adversarial(self):
        rng = random.Random(6302026)
        for _ in range(500):
            n = rng.randrange(1, 31)
            pairs = combinations(range(n), 2)
            density = rng.choice((0.0, 0.03, 0.2, 0.5, 1.0))
            edges = tuple(e for e in pairs if rng.random() < density)
            self.assertEqual(bipartition_rust(n, edges), bipartition(n, edges))
        self.assertIsNone(bipartition_rust(1, ((0, 0),)))
        for n, edges in ((3, ((0, 3),)), (3, ((-1, 1),))):
            with self.assertRaises((ValueError, OverflowError)):
                bipartition_rust(n, edges)


if __name__ == "__main__":
    unittest.main()
