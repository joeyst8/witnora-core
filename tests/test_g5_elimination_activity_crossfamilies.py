"""Independent topology controls for G5 elimination-activity separator hints.

A deliberately small exploratory benchmark: no winners are preselected,
and the assertions enforce only integrity of the comparison.
"""

import json
import random
import statistics
import unittest
from itertools import combinations

from witnora_core.g5_elimination_activity import (
    activity_from_g5_operations,
    ranked_pair_candidates,
)
from witnora_core.operator_genesis import gaussian_eliminate_gf2
from witnora_core.separator_affine_family_theorem import _components_after_removing
from witnora_core.separator_structural_priority import articulation_vertices


def topology_edges(name):
    if name == "cycle8":
        n = 8
        return [(i, (i + 1) % n) for i in range(n)]
    if name == "cycle12":
        n = 12
        return [(i, (i + 1) % n) for i in range(n)]
    if name == "ladder8":
        return [
            (0, 1), (1, 2), (2, 3),
            (4, 5), (5, 6), (6, 7),
            (0, 4), (1, 5), (2, 6), (3, 7),
        ]
    if name == "theta8":
        return [
            (0, 2), (2, 3), (3, 1),
            (0, 4), (4, 5), (5, 1),
            (0, 6), (6, 7), (7, 1),
        ]
    if name == "clique6":
        return list(combinations(range(6), 2))
    raise ValueError(name)


def sizes_after(graph, pair):
    return [
        len(x) for x in _components_after_removing(graph, set(pair))
    ]


class G5ActivityCrossFamilyTest(unittest.TestCase):
    def test_structurally_different_biconnected_graphs(self):
        rng = random.Random(630633)
        names = ("cycle8", "cycle12", "ladder8", "theta8", "clique6")
        records = {}
        for name in names:
            edges = topology_edges(name)
            vertices = sorted({v for edge in edges for v in edge})
            graph_reference = {v: set() for v in vertices}
            for a, b in edges:
                graph_reference[a].add(b)
                graph_reference[b].add(a)
            self.assertEqual(articulation_vertices(graph_reference), ())

            outcomes = []
            for trial in range(48):
                labels = rng.sample(range(1, 512), len(vertices))
                mapping = dict(zip(vertices, labels))
                permuted_edges = list(edges)
                rng.shuffle(permuted_edges)
                equations = [
                    {
                        "variables": [mapping[a], mapping[b]],
                        "parity_bit": 0,
                    }
                    for a, b in permuted_edges
                ]
                elimination = gaussian_eliminate_gf2(equations)
                activity = activity_from_g5_operations(
                    elimination["row_operations"], mapping.values()
                )
                g5_pair = ranked_pair_candidates(activity)[0]
                numeric_pair = tuple(sorted(mapping.values())[:2])
                graph = {v: set() for v in mapping.values()}
                for a, b in permuted_edges:
                    x, y = mapping[a], mapping[b]
                    graph[x].add(y)
                    graph[y].add(x)
                degree_pair = tuple(sorted(graph, key=lambda v: (-len(graph[v]), v))[:2])
                g5_sizes = sizes_after(graph, g5_pair)
                numeric_sizes = sizes_after(graph, numeric_pair)
                degree_sizes = sizes_after(graph, degree_pair)
                outcomes.append({
                    "trial": trial,
                    "g5_split": len(g5_sizes) > 1,
                    "numeric_split": len(numeric_sizes) > 1,
                    "degree_split": len(degree_sizes) > 1,
                    "g5_largest": max(g5_sizes),
                    "numeric_largest": max(numeric_sizes),
                    "degree_largest": max(degree_sizes),
                })
            records[name] = {
                "trials": len(outcomes),
                "g5_split": sum(x["g5_split"] for x in outcomes),
                "numeric_split": sum(x["numeric_split"] for x in outcomes),
                "degree_split": sum(x["degree_split"] for x in outcomes),
                "g5_mean_largest": round(
                    statistics.mean(x["g5_largest"] for x in outcomes), 3
                ),
                "numeric_mean_largest": round(
                    statistics.mean(x["numeric_largest"] for x in outcomes), 3
                ),
                "degree_mean_largest": round(
                    statistics.mean(x["degree_largest"] for x in outcomes), 3
                ),
                "g5_worse_than_degree": sum(
                    x["g5_largest"] > x["degree_largest"]
                    for x in outcomes
                ),
                "g5_worse_largest": sum(
                    x["g5_largest"] > x["numeric_largest"]
                    for x in outcomes
                ),
            }
            self.assertEqual(records[name]["trials"], 48)
            if name == "clique6":
                self.assertEqual(records[name]["g5_split"], 0)
                self.assertEqual(records[name]["numeric_split"], 0)
                self.assertEqual(records[name]["degree_split"], 0)
        print("G5_ACTIVITY_CROSSFAMILY_STUDY", json.dumps(records, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
