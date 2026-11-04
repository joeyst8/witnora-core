"""R-050 native TC-063 articulation and exhaustive singleton hints."""
from __future__ import annotations

import os
import random
import unittest
from witnora_core.separator_structural_priority import (
    articulation_vertices, articulation_vertices_rust,
    prioritized_singletons, prioritized_singletons_rust,
)


def components(graph, removed=None):
    remaining=set(graph) - ({removed} if removed is not None else set())
    count=0
    while remaining:
        count+=1
        seen={remaining.pop()}
        frontier=list(seen)
        while frontier:
            nxt=graph[frontier.pop()] & remaining
            remaining.difference_update(nxt)
            frontier.extend(nxt)
            seen.update(nxt)
    return count


def oracle_articulations(graph):
    base=components(graph)
    return tuple(v for v in sorted(graph) if components(graph,removed=v)>base)


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestNativeArticulation(unittest.TestCase):
    def test_1500_random_undirected_graphs_independent_oracle(self):
        rng=random.Random(50112026)
        cases=0
        for n in range(1,31):
            for case in range(50):
                graph={v:set() for v in range(1,n+1)}
                chance=rng.choice((0.04,0.1,0.2,0.4,0.7))
                for a in range(1,n+1):
                    for b in range(a+1,n+1):
                        if rng.random()<chance:
                            graph[a].add(b)
                            graph[b].add(a)
                with self.subTest(n=n,case=case):
                    expected=articulation_vertices(graph)
                    actual=articulation_vertices_rust(graph)
                    self.assertEqual(actual,expected)
                    self.assertEqual(actual,oracle_articulations(graph))
                    ranked=prioritized_singletons_rust(graph)
                    self.assertEqual(ranked,prioritized_singletons(graph))
                    self.assertEqual(set(ranked),set(graph))
                    self.assertEqual(len(ranked),len(graph))
                    self.assertEqual(
                        set(ranked[:len(actual)]),set(actual))
                cases+=1
        self.assertEqual(cases,1500)

    def test_200_deep_paths_without_recursion(self):
        for n in (2,3,4,8,64,128,512):
            graph={v:set() for v in range(1,n+1)}
            for v in range(1,n):
                graph[v].add(v+1)
                graph[v+1].add(v)
            expected=tuple(range(2,n))
            self.assertEqual(articulation_vertices_rust(graph),expected)
            self.assertEqual(articulation_vertices(graph),expected)

    def test_invalid_graph_rejected_explicitly(self):
        with self.assertRaisesRegex(
                ValueError,"graph must be symmetric"):
            articulation_vertices_rust({1:{2},2:set()})


if __name__=="__main__":
    unittest.main()
