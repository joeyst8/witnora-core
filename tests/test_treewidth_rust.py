"""R-017 exact bounded treewidth ordering differential checks."""
from __future__ import annotations

import os
import random
import unittest

from witnora_core.treewidth import (
    find_elimination_order, verify_elimination_order,
)


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestRustTreewidth(unittest.TestCase):
    def test_1000_seeded_exact_order_and_width_differentials(self):
        rng = random.Random(17172026)
        for n in range(1, 11):
            for _ in range(100):
                graph = {v: set() for v in range(1, n + 1)}
                for u in range(1, n + 1):
                    for v in range(u + 1, n + 1):
                        if rng.random() < rng.choice((0.2, 0.4, 0.65)):
                            graph[u].add(v)
                            graph[v].add(u)
                cap = rng.randrange(5)
                with self.subTest(n=n, cap=cap, graph=graph):
                    expected = find_elimination_order(graph, cap)
                    rust = find_elimination_order(graph, cap, backend="rust")
                    self.assertEqual(rust, expected)
                    if rust is not None:
                        self.assertEqual(
                            verify_elimination_order(graph, rust, backend="rust"),
                            verify_elimination_order(graph, rust))

    def test_empty_cycle_clique_invalid_order_and_finite_cap(self):
        empty = {}
        self.assertEqual(find_elimination_order(empty, 0, backend="rust"), [])
        self.assertEqual(verify_elimination_order(empty, [], backend="rust"), 0)
        graph = {v: set() for v in (1, 2, 3, 4, 5)}
        for v in graph:
            graph[v] = set(graph) - {v}
        self.assertIsNone(find_elimination_order(graph, 3, backend="rust"))
        self.assertIsNotNone(find_elimination_order(graph, 4, backend="rust"))
        self.assertIsNone(verify_elimination_order(
            graph, [1, 1, 2, 3, 4], backend="rust"))
        path = {1: {2}, 2: {1, 3}, 3: {2, 4},
                4: {3, 5}, 5: {4}}
        with self.assertRaises(ValueError):
            find_elimination_order(path, 1, backend="rust", max_rust_states=1)
        with self.assertRaises(ValueError):
            find_elimination_order(path, 5, backend="rust")
        with self.assertRaises(ValueError):
            find_elimination_order(path, 1, backend="unknown")


if __name__ == "__main__":
    unittest.main()
