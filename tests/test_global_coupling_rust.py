"""R-052 exact native two-edge-cut metadata, witness checks and fallback order."""
from __future__ import annotations

import os
import random
import unittest
from itertools import combinations
from math import comb

from witnora_core.global_coupling_separator import (
    two_edge_cut_boundary_pairs,
    two_edge_cut_boundary_pairs_rust,
    prioritized_global_pairs,
    prioritized_global_pairs_rust,
)


def components_oracle(graph, removed_vertices=(), removed_edges=()):
    """Independent breadth-first component oracle, ignoring removed edges."""
    vertices = set(graph) - set(removed_vertices)
    blocked = {frozenset(edge) for edge in removed_edges}
    components = []
    while vertices:
        first = min(vertices)
        vertices.remove(first)
        component = {first}
        queue = [first]
        for vertex in queue:
            for neighbor in graph[vertex]:
                if neighbor in vertices and frozenset((vertex, neighbor)) not in blocked:
                    vertices.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def assert_witness(testcase, graph, candidate):
    separator = candidate["separator"]
    edge_cut = [tuple(edge) for edge in candidate["cut_edges"]]
    sides = components_oracle(graph, removed_edges=edge_cut)
    testcase.assertEqual(len(sides), 2)
    testcase.assertEqual([len(side) for side in sides],
                         candidate["edge_split_sizes"])
    testcase.assertTrue(all(
        (u in sides[0]) != (v in sides[0]) for u, v in edge_cut
    ))
    testcase.assertEqual(
        sorted(len(side) for side in components_oracle(
            graph, removed_vertices=separator
        )),
        candidate["residual_component_sizes"],
    )
    testcase.assertGreater(len(candidate["residual_component_sizes"]), 1)
    testcase.assertTrue(any(
        sorted(v for edge in edge_cut for v in edge if v in side) == separator
        for side in sides
    ))


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "PyO3 wheel installed in dedicated Rust CI")
class TestNativeGlobalCoupling(unittest.TestCase):
    def test_900_random_graphs_and_independent_witnesses(self):
        rng = random.Random(52112026)
        count = 0
        for n in range(12):
            for sample in range(75):
                vertices = rng.sample(range(10, 280), n)
                graph = {v: set() for v in vertices}
                probability = rng.choice((0.0, 0.08, 0.18, 0.3, 0.5, 0.9, 1.0))
                for a, b in combinations(vertices, 2):
                    if rng.random() < probability:
                        graph[a].add(b)
                        graph[b].add(a)
                with self.subTest(n=n, sample=sample):
                    original = two_edge_cut_boundary_pairs(graph)
                    native = two_edge_cut_boundary_pairs_rust(graph)
                    self.assertEqual(native, original)
                    self.assertEqual(native["status"], "DIAGNOSTIC_ONLY")
                    edges = native["edge_count"]
                    self.assertEqual(native["edge_pair_checks"],
                                     comb(edges, 2) if (
                                         graph and len(components_oracle(graph)) == 1
                                     ) else 0)
                    for candidate in native["candidates"]:
                        assert_witness(self, graph, candidate)
                    order = prioritized_global_pairs_rust(graph)
                    self.assertEqual(order, prioritized_global_pairs(graph))
                    self.assertEqual(len(order), comb(n, 2))
                    self.assertEqual(len(set(order)), len(order))
                count += 1
        self.assertEqual(count, 900)

    def test_100_planted_cycle_graphs_with_edge_witnesses(self):
        for n in range(4, 24):
            for variant in range(5):
                vertices = [i * 3 + variant + 1 for i in range(n)]
                graph = {v: set() for v in vertices}
                for a, b in zip(vertices, vertices[1:] + vertices[:1]):
                    graph[a].add(b)
                    graph[b].add(a)
                with self.subTest(n=n, variant=variant):
                    native = two_edge_cut_boundary_pairs_rust(graph)
                    self.assertEqual(native, two_edge_cut_boundary_pairs(graph))
                    self.assertTrue(native["candidates"])
                    for candidate in native["candidates"]:
                        assert_witness(self, graph, candidate)

    def test_invalid_graphs_fail_closed(self):
        for graph in ({1: {1}}, {1: {2}, 2: set()}, {1: {4}}):
            with self.assertRaises(ValueError):
                two_edge_cut_boundary_pairs_rust(graph)
            with self.assertRaises(ValueError):
                two_edge_cut_boundary_pairs(graph)


if __name__ == "__main__":
    unittest.main()
