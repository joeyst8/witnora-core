"""Complete two-vertex-cut probe via one-deletion articulation scans."""

import json
import random
import unittest
from itertools import combinations

from tests.test_g5_pairwise_dense_bridge import regular_two_cut_edges
from tests.test_global_coupling_separator import graph_of, two_cut_oracle
from witnora_core.cnf import CNFFormula
from witnora_core.global_coupling_separator import two_edge_cut_boundary_pairs
from witnora_core.separator_affine_family_theorem import (
    SEPARATOR_AFFINE_FAMILY_RECOGNIZED,
    _components_after_removing,
    recognize_separator_affine_family,
)
from witnora_core.separator_structural_priority import articulation_vertices
from witnora_core.vertex_coupling_separator import (
    vertex_coupling_pairs,
    prioritized_vertex_pairs,
)
from witnora_core.xor import canonical_xor_cnf_clauses


class VertexCouplingSeparatorTest(unittest.TestCase):
    def test_dense_regular_two_cut_family_complete_under_relabeling(self):
        rng = random.Random(630637)
        results = {}
        for k in (4, 5, 6, 7):
            edges = regular_two_cut_edges(k)
            n = 2 * k
            for _ in range(48):
                ids = rng.sample(range(1, 4096), n)
                mapping = dict(enumerate(ids))
                shuffled = list(edges)
                rng.shuffle(shuffled)
                graph = graph_of(ids, [
                    (mapping[a], mapping[b]) for a, b in shuffled
                ])
                exact = two_cut_oracle(graph)
                self.assertEqual(len(exact), 4)
                report = vertex_coupling_pairs(graph)
                predicted = {
                    tuple(row["separator"]) for row in report["candidates"]
                }
                self.assertTrue(report["complete_for_two_vertex_cuts"])
                self.assertEqual(report["articulation_scans"], n)
                self.assertEqual(predicted, exact)
                self.assertEqual(
                    set(prioritized_vertex_pairs(graph)[:len(predicted)]), exact
                )
            results[n] = {
                "trials": 48,
                "all_four_cuts_found": 48,
                "articulation_scans_per_trial": n,
                "edge_cut_pair_checks_per_trial": len(edges) * (len(edges) - 1) // 2,
            }
        print("VERTEX_COUPLING_DENSE_BRIDGE_SCALE", json.dumps(results, sort_keys=True))

    def test_overlapping_dense_cliques_are_detected(self):
        blocks = ((0, 1, 2, 3, 4), (0, 1, 5, 6, 7))
        edge_set = set().union(*(set(combinations(block, 2)) for block in blocks))
        labels = {0: 100, 1: 101, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6}
        edges = [(labels[a], labels[b]) for a, b in sorted(edge_set)]
        graph = graph_of(labels.values(), edges)
        self.assertEqual(two_cut_oracle(graph), {(100, 101)})
        self.assertEqual(two_edge_cut_boundary_pairs(graph)["candidates"], [])
        self.assertEqual(
            {tuple(row["separator"]) for row in vertex_coupling_pairs(graph)["candidates"]},
            {(100, 101)},
        )
        self.assertEqual(prioritized_vertex_pairs(graph)[0], (100, 101))

        clauses = [
            clause
            for a, b in edges
            for clause in canonical_xor_cnf_clauses((a, b), 0)
        ]
        formula = CNFFormula.from_raw_clauses(clauses)
        recognition = recognize_separator_affine_family(
            formula, c=2, r=2, priority="vertex_coupling"
        )
        self.assertEqual(recognition["status"], SEPARATOR_AFFINE_FAMILY_RECOGNIZED)
        self.assertEqual(recognition["separator_variables"], [100, 101])
        self.assertEqual(recognition["candidates_examined"], 9)
        self.assertTrue(recognition["trace"][-1]["accepted"])

    def test_random_2connected_graphs_match_independent_full_oracle(self):
        rng = random.Random(630638)
        checked = 0
        for n in range(4, 10):
            for _ in range(120):
                p = rng.choice((0.3, 0.5, 0.7, 0.9))
                edges = [
                    (a, b) for a, b in combinations(range(n), 2)
                    if rng.random() < p
                ]
                graph = graph_of(range(n), edges)
                if len(_components_after_removing(graph, set())) != 1:
                    continue
                if articulation_vertices(graph):
                    continue
                report = vertex_coupling_pairs(graph)
                self.assertTrue(report["complete_for_two_vertex_cuts"])
                self.assertEqual(
                    {tuple(row["separator"]) for row in report["candidates"]},
                    two_cut_oracle(graph),
                )
                checked += 1
        self.assertGreater(checked, 250)
        print("VERTEX_COUPLING_INDEPENDENT_RANDOM_ORACLE", checked)

    def test_no_cuts_and_out_of_domain_inputs(self):
        controls = (
            graph_of(range(6), combinations(range(6), 2)),
            graph_of(range(8), [
                (a, b) for a, b in combinations(range(8), 2)
                if (a ^ b).bit_count() == 1
            ]),
            graph_of(range(8), (
                [(0, v) for v in range(1, 8)]
                + [(v, v + 1) for v in range(1, 7)]
                + [(1, 7)]
            )),
        )
        for graph in controls:
            self.assertEqual(two_cut_oracle(graph), set())
            report = vertex_coupling_pairs(graph)
            self.assertEqual(report["candidates"], [])
            self.assertTrue(report["complete_for_two_vertex_cuts"])
        path = graph_of(range(5), [(0, 1), (1, 2), (2, 3), (3, 4)])
        self.assertFalse(vertex_coupling_pairs(path)["complete_for_two_vertex_cuts"])
        self.assertEqual(vertex_coupling_pairs(path)["candidates"], [])
        self.assertEqual(
            prioritized_vertex_pairs(path),
            tuple(combinations(range(5), 2)),
        )
        disconnected = {0: set(), 1: set()}
        self.assertFalse(
            vertex_coupling_pairs(disconnected)["complete_for_two_vertex_cuts"]
        )


if __name__ == "__main__":
    unittest.main()
