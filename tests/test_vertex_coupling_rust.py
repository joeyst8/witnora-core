"""R-051 graph-theoretic complete two-vertex cuts and exhaustive fallback."""
from __future__ import annotations

import os
import random
import unittest
from itertools import combinations

from witnora_core.vertex_coupling_separator import (
    vertex_coupling_pairs, vertex_coupling_pairs_rust,
    prioritized_vertex_pairs, prioritized_vertex_pairs_rust,
)


def ncomponents(graph,removed=()):
    remaining=set(graph)-set(removed)
    parts=0
    while remaining:
        parts+=1
        frontier=[remaining.pop()]
        while frontier:
            v=frontier.pop()
            adjacent=graph[v] & remaining
            remaining.difference_update(adjacent)
            frontier.extend(adjacent)
    return parts


def complete_pairs_oracle(graph):
    if len(graph)<3 or ncomponents(graph)!=1:
        return None
    if any(ncomponents(graph,(v,))>1 for v in graph):
        return None
    return [
        pair for pair in combinations(sorted(graph),2)
        if ncomponents(graph,pair)>1
    ]


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestNativeVertexCoupling(unittest.TestCase):
    def test_900_random_graphs_exact_reporting_and_oracle(self):
        rng=random.Random(51112026)
        cases=0
        for n in range(3,18):
            for case in range(60):
                graph={v:set() for v in range(1,n+1)}
                p=rng.choice((0.05,0.1,0.2,0.35,0.6,0.9))
                for a,b in combinations(graph,2):
                    if rng.random()<p:
                        graph[a].add(b)
                        graph[b].add(a)
                with self.subTest(n=n,case=case):
                    original=vertex_coupling_pairs(graph)
                    native=vertex_coupling_pairs_rust(graph)
                    self.assertEqual(native,original)
                    self.assertEqual(native["status"],"DIAGNOSTIC_ONLY")
                    oracle=complete_pairs_oracle(graph)
                    self.assertEqual(native["complete_for_two_vertex_cuts"],
                                     oracle is not None)
                    if oracle is not None:
                        self.assertEqual(
                            [tuple(x["separator"]) for x in native["candidates"]],
                            oracle)
                    order=prioritized_vertex_pairs_rust(graph)
                    self.assertEqual(order,prioritized_vertex_pairs(graph))
                    self.assertEqual(len(order),n*(n-1)//2)
                cases+=1
        self.assertEqual(cases,900)

    def test_100_planted_cycles_nonadjacent_cuts(self):
        for n in range(4,104):
            graph={v:{(v-2)%n+1,v%n+1} for v in range(1,n+1)}
            with self.subTest(n=n):
                native=vertex_coupling_pairs_rust(graph)
                self.assertEqual(native,vertex_coupling_pairs(graph))
                self.assertTrue(native["complete_for_two_vertex_cuts"])
                self.assertEqual(native["articulation_scans"],n)

    def test_invalid_inputs_preserve_strict_graph_domain(self):
        for graph in ({1:{1}}, {1:{2},2:set()}):
            with self.assertRaises(ValueError):
                vertex_coupling_pairs_rust(graph)
            with self.assertRaises(ValueError):
                vertex_coupling_pairs(graph)


if __name__=="__main__":
    unittest.main()
