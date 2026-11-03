"""Exhaustive finite refinement oracle for Python articulation and 2-cut scans.

Every labeled simple undirected graph with up to six vertices is tested
against an independently implemented component-count oracle. This is
finite evidence only, not a universal Python-to-Lean semantics proof.
"""

import json
import random
import unittest
from itertools import combinations

from witnora_core.separator_structural_priority import articulation_vertices
from witnora_core.vertex_coupling_separator import vertex_coupling_pairs


def oracle_component_count(graph, removed=frozenset()):
    """Simple independent breadth-first connectivity oracle."""
    unseen = set(graph) - set(removed)
    components = 0
    while unseen:
        components += 1
        frontier = [min(unseen)]
        unseen.remove(frontier[0])
        while frontier:
            vertex = frontier.pop(0)
            for neighbor in graph[vertex]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    frontier.append(neighbor)
    return components


def graph_by_edge_mask(n, mask):
    vertices = list(range(n))
    graph = {v: set() for v in vertices}
    for index, (a, b) in enumerate(combinations(vertices, 2)):
        if (mask >> index) & 1:
            graph[a].add(b)
            graph[b].add(a)
    return graph


class VertexCouplingExhaustiveTest(unittest.TestCase):
    def test_all_labeled_simple_graphs_up_to_six_vertices(self):
        report = {}
        for n in range(1, 7):
            cases = 1 << (n * (n - 1) // 2)
            eligible = 0
            real_two_cuts = 0
            for mask in range(cases):
                graph = graph_by_edge_mask(n, mask)
                baseline = oracle_component_count(graph)
                expected_articulations = {
                    v for v in graph
                    if oracle_component_count(graph, frozenset((v,))) > baseline
                }
                self.assertEqual(
                    set(articulation_vertices(graph)), expected_articulations,
                    msg=f"n={n},mask={mask},articulation",
                )
                if n < 3 or baseline != 1 or expected_articulations:
                    continue
                eligible += 1
                expected_pairs = {
                    pair for pair in combinations(range(n), 2)
                    if oracle_component_count(graph, frozenset(pair)) > 1
                }
                result = vertex_coupling_pairs(graph)
                self.assertTrue(result["complete_for_two_vertex_cuts"])
                self.assertEqual(
                    {tuple(row["separator"]) for row in result["candidates"]},
                    expected_pairs,
                    msg=f"n={n},mask={mask},two_cut",
                )
                real_two_cuts += len(expected_pairs)
            report[n] = {
                "all_labeled_graphs": cases,
                "connected_without_articulation": eligible,
                "total_two_cut_witnesses": real_two_cuts,
            }
        print("VERTEX_COUPLING_EXHAUSTIVE_LABELED", json.dumps(report, sort_keys=True))

    def test_relabeling_and_neighbor_order_independence(self):
        rng = random.Random(630640)
        comparisons = 0
        for n in (6, 8, 10):
            for _ in range(100):
                graph = {
                    v: set(w for w in range(n) if w != v and
                           ((min(v, w), max(v, w)) in set()))
                    for v in range(n)
                }
                # Build a symmetric random graph and scramble insertion order.
                edges = [
                    (a, b) for a, b in combinations(range(n), 2)
                    if rng.random() < rng.choice((0.3, 0.6, 0.9))
                ]
                labels = dict(enumerate(rng.sample(range(1, 10000), n)))
                shuffled_vertices = list(range(n))
                rng.shuffle(shuffled_vertices)
                shuffled_edges = list(edges)
                rng.shuffle(shuffled_edges)
                relabeled = {labels[v]: set() for v in shuffled_vertices}
                for a, b in shuffled_edges:
                    relabeled[labels[a]].add(labels[b])
                    relabeled[labels[b]].add(labels[a])
                baseline = oracle_component_count(relabeled)
                expected = {
                    v for v in relabeled
                    if oracle_component_count(relabeled, frozenset((v,))) > baseline
                }
                self.assertEqual(set(articulation_vertices(relabeled)), expected)
                if baseline == 1 and not expected:
                    observed = {
                        tuple(row["separator"])
                        for row in vertex_coupling_pairs(relabeled)["candidates"]
                    }
                    oracle = {
                        pair for pair in combinations(sorted(relabeled), 2)
                        if oracle_component_count(relabeled, frozenset(pair)) > 1
                    }
                    self.assertEqual(observed, oracle)
                comparisons += 1
        print("VERTEX_COUPLING_RELABELING_ORACLE", comparisons)


if __name__ == "__main__":
    unittest.main()
