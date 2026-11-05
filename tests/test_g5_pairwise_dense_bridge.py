"""Scale probe for pairwise G5 cross-merge hints on regular 2-cut graphs.

Two K_(d+1) graphs each lose one edge; disjoint cross edges restore
regular degree d while leaving a small two-vertex separator. The graph
has no articulation vertex and no useful degree variation.
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


def regular_two_cut_edges(block_size):
    left = [
        (a, b) for a, b in combinations(range(block_size), 2)
        if (a, b) != (0, 1)
    ]
    right = [
        (a, b)
        for a, b in combinations(range(block_size, 2 * block_size), 2)
        if (a, b) != (block_size, block_size + 1)
    ]
    return left + right + [(0, block_size), (1, block_size + 1)]


def partition_metric(graph, pair):
    pieces = _components_after_removing(graph, set(pair))
    return {"split": len(pieces) > 1, "largest": max(len(p) for p in pieces)}


class G5PairwiseDenseBridgeTest(unittest.TestCase):
    def test_regular_two_cut_family_scales(self):
        rng = random.Random(630635)
        report = {}
        for block_size in (4, 5, 6, 7):
            edges = regular_two_cut_edges(block_size)
            n = 2 * block_size
            skeleton = {v: set() for v in range(n)}
            for a, b in edges:
                skeleton[a].add(b)
                skeleton[b].add(a)
            self.assertEqual(articulation_vertices(skeleton), ())
            self.assertEqual({len(neighbors) for neighbors in skeleton.values()}, {block_size - 1})
            self.assertGreater(
                len(_components_after_removing(skeleton, {0, 1})), 1
            )
            actual_two_cuts = {
                pair for pair in combinations(range(n), 2)
                if len(_components_after_removing(skeleton, set(pair))) > 1
            }
            expected_two_cuts = {
                (0, 1),
                (0, block_size + 1),
                (1, block_size),
                (block_size, block_size + 1),
            }
            self.assertEqual(actual_two_cuts, expected_two_cuts)
            records = []
            for trial in range(48):
                mapped = dict(zip(range(n), rng.sample(range(1, 2048), n)))
                ordered_edges = list(edges)
                rng.shuffle(ordered_edges)
                equations = [
                    {"variables": [mapped[a], mapped[b]], "parity_bit": 0}
                    for a, b in ordered_edges
                ]
                result = gaussian_eliminate_gf2(equations)
                ops = result["row_operations"]
                activity = activity_from_g5_operations(ops, mapped.values())
                pairwise = pairwise_cross_merge_activity(ops, mapped.values())
                graph = {v: set() for v in mapped.values()}
                for a, b in ordered_edges:
                    graph[mapped[a]].add(mapped[b])
                    graph[mapped[b]].add(mapped[a])
                candidate_pairs = {
                    "numeric": tuple(sorted(graph)[:2]),
                    "single": ranked_pair_candidates(activity)[0],
                    "pairwise": pairwise["ranked_pairs"][0],
                }
                records.append({
                    name: partition_metric(graph, candidate)
                    for name, candidate in candidate_pairs.items()
                })
            summary = {
                "trials": len(records),
                "exact_two_cuts": len(actual_two_cuts),
                "possible_pairs": n * (n - 1) // 2,
            }
            for method in ("numeric", "single", "pairwise"):
                summary[method + "_split"] = sum(
                    rec[method]["split"] for rec in records
                )
                summary[method + "_largest"] = round(
                    statistics.mean(rec[method]["largest"] for rec in records), 3
                )
            report[str(n)] = summary
            self.assertEqual(summary["trials"], 48)
        print("G5_PAIRWISE_DENSE_BRIDGE_SCALE", json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
