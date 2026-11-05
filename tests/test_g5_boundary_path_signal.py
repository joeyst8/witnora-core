"""Track B falsification study of indexed G5 edge-lineage boundary paths.

A G5-derived pair is only a candidate. Exact deletion-component tests
measure whether the path heuristic finds useful cuts, and wheel/cube
controls expose the possibility of false separator predictions.
"""

import json
import random
import statistics
import unittest

from witnora_core.g5_boundary_path_signal import (
    boundary_path_candidates_from_g5,
)
from witnora_core.g5_elimination_activity import (
    activity_from_g5_operations,
    ranked_pair_candidates,
    pairwise_cross_merge_activity,
)
from witnora_core.operator_genesis import gaussian_eliminate_gf2
from witnora_core.separator_affine_family_theorem import _components_after_removing
from tests.test_g5_activity_hybrid_heldout import heldout_edges


def _graph(edges):
    vertices = {v for edge in edges for v in edge}
    graph = {v: set() for v in vertices}
    for a, b in edges:
        graph[a].add(b)
        graph[b].add(a)
    return graph


def _quality(graph, pair):
    if not pair:
        return {"split": False, "largest": len(graph)}
    components = _components_after_removing(graph, set(pair))
    return {
        "split": len(components) > 1,
        "largest": max(map(len, components), default=0),
    }


def _run_trace(edges):
    equations = [
        {"variables": [a, b], "parity_bit": 0}
        for a, b in edges
    ]
    result = gaussian_eliminate_gf2(equations)
    rows = result["gaussian_elimination_trace"][0]["rows"]
    return rows, result["row_operations"]


class G5BoundaryPathStudy(unittest.TestCase):
    def test_cycle_family_relabeling_and_balance(self):
        rng = random.Random(630639)
        report = {}
        for n in (8, 16, 32):
            base_edges = [(i, (i + 1) % n) for i in range(n)]
            observations = []
            for trial in range(48):
                labels = rng.sample(range(1, 17000000), n)
                mapping = dict(enumerate(labels))
                edges = [(mapping[a], mapping[b]) for a, b in base_edges]
                rng.shuffle(edges)
                graph = _graph(edges)
                initial, ops = _run_trace(edges)
                signal = boundary_path_candidates_from_g5(initial, ops)
                self.assertEqual(signal["status"], "DIAGNOSTIC_ONLY")
                self.assertEqual(signal["xor_operations"],
                                 sum(op["operation"] == "ADD_ROW_XOR"
                                     for op in ops))
                pairs = [tuple(item["separator"]) for item in signal["candidates"]]
                self.assertEqual(len(pairs), len(set(pairs)))
                for item in signal["candidates"]:
                    self.assertGreater(item["balance_proxy"], 0)
                    # This property is specific to an *un-chorded cycle*:
                    # a proper path and its complementary path are separated
                    # by removing their two common endpoints.
                    self.assertTrue(_quality(graph, item["separator"])["split"])

                activity = activity_from_g5_operations(ops, graph)
                pairwise = pairwise_cross_merge_activity(ops, graph)
                suggestions = {
                    "boundary_path": pairs[0] if pairs else (),
                    "activity": ranked_pair_candidates(activity)[0],
                    "cross_merge": pairwise["ranked_pairs"][0],
                    "numeric": tuple(sorted(graph)[:2]),
                }
                observations.append({
                    method: _quality(graph, candidate)
                    for method, candidate in suggestions.items()
                })
            report[str(n)] = {
                "trials": len(observations),
                "path_candidate_trials": sum(
                    item["boundary_path"]["split"] for item in observations
                ),
                **{
                    f"{method}_cuts": sum(x[method]["split"] for x in observations)
                    for method in ("boundary_path", "activity",
                                   "cross_merge", "numeric")
                },
                **{
                    f"{method}_mean_largest": round(statistics.mean(
                        x[method]["largest"] for x in observations
                    ), 3)
                    for method in ("boundary_path", "activity",
                                   "cross_merge", "numeric")
                },
                "path_better_balance_than_activity": sum(
                    x["boundary_path"]["largest"] < x["activity"]["largest"]
                    for x in observations
                ),
                "path_worse_balance_than_activity": sum(
                    x["boundary_path"]["largest"] > x["activity"]["largest"]
                    for x in observations
                ),
            }
            self.assertEqual(report[str(n)]["trials"], 48)
        print("G5_BOUNDARY_PATH_CYCLE_STUDY", json.dumps(report, sort_keys=True))

    def test_no_two_cut_controls_are_not_promoted(self):
        rng = random.Random(630640)
        report = {}
        for name in ("wheel8_no_two_cut", "cube8_no_two_cut"):
            edges = heldout_edges(name)
            vertices = sorted({v for a, b in edges for v in (a, b)})
            proposed = 0
            verified = 0
            for _ in range(32):
                labels = rng.sample(range(1, 1024), len(vertices))
                mapping = dict(zip(vertices, labels))
                mapped = [(mapping[a], mapping[b]) for a, b in edges]
                rng.shuffle(mapped)
                graph = _graph(mapped)
                initial, ops = _run_trace(mapped)
                signal = boundary_path_candidates_from_g5(initial, ops)
                proposed += len(signal["candidates"])
                for candidate in signal["candidates"]:
                    verified += int(_quality(graph, candidate["separator"])["split"])
            report[name] = {"proposed_paths": proposed,
                            "actual_two_cuts": verified,
                            "trials": 32}
            self.assertEqual(verified, 0)
        print("G5_BOUNDARY_PATH_NO_CUT_CONTROLS",
              json.dumps(report, sort_keys=True))

    def test_replay_rejects_forged_row_snapshot(self):
        initial, operations = _run_trace(
            [(1, 2), (2, 3), (3, 4), (4, 1)]
        )
        forged = [dict(op) for op in operations]
        index = next(i for i, op in enumerate(forged)
                     if op["operation"] == "ADD_ROW_XOR")
        forged[index]["after"] = {"coefficients": [999999], "rhs": 0}
        with self.assertRaisesRegex(ValueError, "snapshot disagrees"):
            boundary_path_candidates_from_g5(initial, forged)


if __name__ == "__main__":
    unittest.main()
