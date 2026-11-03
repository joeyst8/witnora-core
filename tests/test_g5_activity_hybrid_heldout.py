"""Held-out challenge for a degree/G5 activity hybrid separator rule.

The rule was suggested by cycle/ladder/theta pilots. This file uses
different topologies and a fresh seed. It reports failures and makes
no theorem or runtime-speed claim.
"""

import json
import random
import statistics
import unittest
from itertools import combinations

from witnora_core.g5_elimination_activity import (
    activity_from_g5_operations,
    ranked_pair_candidates,
    pairwise_cross_merge_activity,
)
from witnora_core.operator_genesis import gaussian_eliminate_gf2
from witnora_core.separator_affine_family_theorem import _components_after_removing
from witnora_core.separator_structural_priority import articulation_vertices


def heldout_edges(name):
    if name == "chorded_cycle8":
        return [(i, (i + 1) % 8) for i in range(8)] + [(0, 4)]
    if name == "edge_glued_cycles6":
        return [
            (0, 1), (0, 2), (2, 3), (3, 1),
            (0, 4), (4, 5), (5, 1),
        ]
    if name == "regular_two_cut8":
        # Each K4 loses an edge, then the two missing-edge endpoints
        # receive one cross edge. Degree is uniformly three, but
        # removing {0,1} separates the two dense halves.
        left = [
            (a, b) for a, b in combinations(range(4), 2)
            if (a, b) != (0, 1)
        ]
        right = [
            (a, b) for a, b in combinations(range(4, 8), 2)
            if (a, b) != (4, 5)
        ]
        return left + right + [(0, 4), (1, 5)]
    if name == "wheel8_no_two_cut":
        return [
            (i, 1 + ((i - 1 + 1) % 7)) for i in range(1, 8)
        ] + [(0, i) for i in range(1, 8)]
    if name == "cube8_no_two_cut":
        return [
            (v, v ^ (1 << bit))
            for v in range(8) for bit in range(3)
            if v < (v ^ (1 << bit))
        ]
    raise ValueError(name)


def quality(graph, pair):
    sizes = [
        len(c) for c in _components_after_removing(graph, set(pair))
    ]
    return {"split": len(sizes) > 1, "largest": max(sizes)}


class G5HybridHeldoutStudy(unittest.TestCase):
    def test_fresh_topology_hybrid_challenge(self):
        rng = random.Random(630634)
        report = {}
        for name in (
            "chorded_cycle8", "edge_glued_cycles6",
            "regular_two_cut8", "wheel8_no_two_cut", "cube8_no_two_cut"
        ):
            edges = heldout_edges(name)
            variables = sorted({v for edge in edges for v in edge})
            base_graph = {v: set() for v in variables}
            for a, b in edges:
                base_graph[a].add(b)
                base_graph[b].add(a)
            self.assertEqual(articulation_vertices(base_graph), ())
            rows = []
            for trial in range(48):
                labels = rng.sample(range(1, 512), len(variables))
                mapping = dict(zip(variables, labels))
                permuted = list(edges)
                rng.shuffle(permuted)
                equations = [
                    {"variables": [mapping[a], mapping[b]], "parity_bit": 0}
                    for a, b in permuted
                ]
                trace = gaussian_eliminate_gf2(equations)
                activity = activity_from_g5_operations(
                    trace["row_operations"], mapping.values()
                )
                graph = {v: set() for v in mapping.values()}
                for a, b in permuted:
                    graph[mapping[a]].add(mapping[b])
                    graph[mapping[b]].add(mapping[a])
                g5_pair = ranked_pair_candidates(activity)[0]
                pairwise = pairwise_cross_merge_activity(
                    trace["row_operations"], mapping.values()
                )
                pairwise_pair = pairwise["ranked_pairs"][0]
                degree_pair = tuple(sorted(
                    graph, key=lambda v: (-len(graph[v]), v)
                )[:2])
                uniform_degree = len({len(graph[v]) for v in graph}) == 1
                hybrid_pair = g5_pair if uniform_degree else degree_pair
                rows.append({
                    "g5": quality(graph, g5_pair),
                    "pairwise": quality(graph, pairwise_pair),
                    "degree": quality(graph, degree_pair),
                    "hybrid": quality(graph, hybrid_pair),
                    "used_g5": uniform_degree,
                })
            report[name] = {
                "trials": len(rows),
                "hybrid_used_g5": sum(r["used_g5"] for r in rows),
                **{
                    f"{method}_{key}": (
                        sum(r[method]["split"] for r in rows)
                        if key == "split"
                        else round(
                            statistics.mean(r[method]["largest"] for r in rows), 3
                        )
                    )
                    for method in ("g5", "pairwise", "degree", "hybrid")
                    for key in ("split", "largest")
                },
            }
            self.assertEqual(report[name]["trials"], 48)
            if name.endswith("no_two_cut"):
                self.assertEqual(report[name]["hybrid_split"], 0)
        print("G5_ACTIVITY_HYBRID_HELDOUT", json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
