"""Adversarial graph and real-G14 checks for two-edge-cut global coupling."""

import json
import random
import unittest
from itertools import combinations

from tests.test_g5_pairwise_dense_bridge import regular_two_cut_edges
from witnora_core.cnf import CNFFormula
from witnora_core.global_coupling_separator import (
    prioritized_global_pairs,
    two_edge_cut_boundary_pairs,
)
from witnora_core.separator_affine_family_theorem import (
    SEPARATOR_AFFINE_FAMILY_RECOGNIZED,
    _components_after_removing,
    recognize_separator_affine_family,
)
from witnora_core.xor import canonical_xor_cnf_clauses


def graph_of(vertices, edges):
    graph = {v: set() for v in vertices}
    for a, b in edges:
        graph[a].add(b)
        graph[b].add(a)
    return graph


def two_cut_oracle(graph):
    return {
        pair for pair in combinations(sorted(graph), 2)
        if len(_components_after_removing(graph, set(pair))) > 1
    }


def parts_after_edge_deletion(graph, cut_edges):
    reduced = {v: set(neighbors) for v, neighbors in graph.items()}
    for a, b in cut_edges:
        reduced[a].remove(b)
        reduced[b].remove(a)
    return _components_after_removing(reduced, set())


class GlobalCouplingSeparatorTest(unittest.TestCase):
    def test_hidden_regular_two_cut_relabeling_scale(self):
        rng = random.Random(630636)
        summary = {}
        for k in (4, 5, 6, 7):
            edges = regular_two_cut_edges(k)
            n = 2 * k
            records = []
            for _ in range(48):
                mapping = dict(zip(range(n), rng.sample(range(1, 2048), n)))
                shuffled = list(edges)
                rng.shuffle(shuffled)
                graph = graph_of(mapping.values(), [
                    (mapping[a], mapping[b]) for a, b in shuffled
                ])
                exact = two_cut_oracle(graph)
                expected_sides = {
                    tuple(sorted((mapping[0], mapping[1]))),
                    tuple(sorted((mapping[k], mapping[k + 1]))),
                }
                self.assertEqual(len(exact), 4)
                self.assertTrue(expected_sides.issubset(exact))
                report = two_edge_cut_boundary_pairs(graph)
                proposals = {
                    tuple(row["separator"]) for row in report["candidates"]
                }
                self.assertEqual(report["status"], "DIAGNOSTIC_ONLY")
                self.assertEqual(report["edge_pair_checks"], len(edges) * (len(edges) - 1) // 2)
                self.assertTrue(expected_sides.issubset(proposals))
                self.assertTrue(proposals.issubset(exact))
                self.assertEqual(proposals, set(prioritized_global_pairs(graph)[:len(proposals)]))
                for row in report["candidates"]:
                    self.assertEqual(len(parts_after_edge_deletion(
                        graph, row["cut_edges"]
                    )), 2)
                    self.assertGreater(len(_components_after_removing(
                        graph, set(row["separator"])
                    )), 1)
                records.append({
                    "first_is_cut": tuple(report["candidates"][0]["separator"]) in exact,
                    "proposals": len(proposals),
                    "checks": report["edge_pair_checks"],
                })
            summary[n] = {
                "trials": len(records),
                "first_is_cut": sum(row["first_is_cut"] for row in records),
                "proposals_min": min(row["proposals"] for row in records),
                "proposals_max": max(row["proposals"] for row in records),
                "edge_pair_checks": records[0]["checks"],
                "exact_two_cuts": 4,
            }
            self.assertEqual(summary[n]["first_is_cut"], 48)
        print("GLOBAL_COUPLING_DENSE_BRIDGE_SCALE", json.dumps(summary, sort_keys=True))

    def test_negative_graph_controls(self):
        cube_vertices = list(range(8))
        cube_edges = [
            (a, b) for a, b in combinations(cube_vertices, 2)
            if (a ^ b).bit_count() == 1
        ]
        wheel_edges = [
            (0, v) for v in range(1, 8)
        ] + [(v, v + 1) for v in range(1, 7)] + [(1, 7)]
        clique_edges = list(combinations(range(6), 2))
        for vertices, edges in (
            (cube_vertices, cube_edges),
            (list(range(8)), wheel_edges),
            (list(range(6)), clique_edges),
        ):
            graph = graph_of(vertices, edges)
            self.assertEqual(two_cut_oracle(graph), set())
            self.assertEqual(two_edge_cut_boundary_pairs(graph)["candidates"], [])
            self.assertEqual(prioritized_global_pairs(graph), tuple(combinations(sorted(graph), 2)))

    def test_reject_bad_graph_and_disconnected_inputs(self):
        with self.assertRaises(ValueError):
            two_edge_cut_boundary_pairs({1: {2}, 2: set()})
        with self.assertRaises(ValueError):
            two_edge_cut_boundary_pairs({1: {1}})
        self.assertEqual(
            two_edge_cut_boundary_pairs({1: set(), 2: set()})["candidates"], []
        )

    def test_actual_g14_recognition_keeps_certificate_checks(self):
        k = 4
        mapping = dict(zip(range(8), (100, 99, 13, 14, 200, 198, 16, 17)))
        edges = [
            (mapping[a], mapping[b]) for a, b in regular_two_cut_edges(k)
        ]
        graph = graph_of(mapping.values(), edges)
        selected = tuple(two_edge_cut_boundary_pairs(graph)["candidates"][0]["separator"])
        self.assertNotEqual(selected, tuple(sorted(graph)[:2]))
        clauses = [
            clause
            for a, b in edges
            for clause in canonical_xor_cnf_clauses((a, b), 0)
        ]
        formula = CNFFormula.from_raw_clauses(clauses)
        recognized = recognize_separator_affine_family(
            formula, c=2, r=2, priority="global_coupling"
        )
        self.assertEqual(recognized["status"], SEPARATOR_AFFINE_FAMILY_RECOGNIZED)
        self.assertEqual(recognized["candidate_priority"], "global_coupling")
        self.assertEqual(tuple(recognized["separator_variables"]), selected)
        self.assertEqual(recognized["candidates_examined"], len(graph) + 1)
        self.assertTrue(recognized["trace"][-1]["accepted"])


if __name__ == "__main__":
    unittest.main()
