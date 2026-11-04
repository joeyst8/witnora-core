"""R-055 native indexed G5 provenance path signals and independent replay."""
from __future__ import annotations

from collections import defaultdict
import os
import random
import unittest

from witnora_core.g5_boundary_path_signal import (
    boundary_path_candidates_from_g5,
    boundary_path_candidates_from_g5_rust,
)


def row(support):
    return {"coefficients": sorted(support)}


def independent_candidate_audit(initial, operations, report):
    """Separate original-edge provenance replay and BFS path topology oracle."""
    live = [set(x["coefficients"]) for x in initial]
    provenance = [{i} for i in range(len(initial))]
    edges = [tuple(sorted(x["coefficients"])) for x in initial]
    universe = set().union(*live) if live else set()
    indexed = defaultdict(list)
    for candidate in report["candidates"]:
        indexed[candidate["operation_index"]].append(candidate)
    for opid, operation in enumerate(operations):
        if operation["operation"] == "SWAP_ROWS":
            a, b = operation["row_a"], operation["row_b"]
            live[a], live[b] = live[b], live[a]
            provenance[a], provenance[b] = provenance[b], provenance[a]
        else:
            target, source = operation["target_row"], operation["source_row"]
            live[target] ^= live[source]
            provenance[target] ^= provenance[source]
            for candidate in indexed[opid]:
                edge_ids = provenance[target]
                graph = defaultdict(set)
                unique_edges = set()
                for edge_id in edge_ids:
                    u, v = edges[edge_id]
                    unique_edges.add((u, v))
                    graph[u].add(v)
                    graph[v].add(u)
                endpoints = set(candidate["separator"])
                assert len(unique_edges) == len(edge_ids)
                assert len(graph) == len(edge_ids) + 1
                assert {u for u in graph if len(graph[u]) == 1} == endpoints
                assert all(len(graph[u]) == 2 for u in graph if u not in endpoints)
                remaining = set(graph)
                frontier = [next(iter(remaining))]
                visited = set(frontier)
                while frontier:
                    for v in graph[frontier.pop()]:
                        if v not in visited:
                            visited.add(v)
                            frontier.append(v)
                assert visited == remaining
                interior = len(graph)-2
                outside = len(universe)-len(endpoints)-interior
                assert candidate["path_interior"] == interior
                assert candidate["path_edges"] == len(edge_ids)
                assert candidate["balance_proxy"] == min(interior, outside)


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated CI")
class TestNativeG5BoundaryPaths(unittest.TestCase):
    def test_900_random_valid_streams_exact_python_parity(self):
        rng = random.Random(55112026)
        for case in range(900):
            size = rng.randrange(2, 12)
            vertex_labels = rng.sample(range(1, 300), size)
            count = rng.randrange(0, 11)
            initial = [row(rng.sample(vertex_labels, 2)) for _ in range(count)]
            live = [set(x["coefficients"]) for x in initial]
            operations = []
            for _ in range(rng.randrange(0, 18) if count else 0):
                if rng.random() < 0.3 or count == 1:
                    a, b = rng.randrange(count), rng.randrange(count)
                    live[a], live[b] = live[b], live[a]
                    op = {"operation": "SWAP_ROWS", "row_a": a, "row_b": b}
                    if rng.random() < 0.5:
                        op["rows_after"] = [row(s) for s in live]
                    operations.append(op)
                else:
                    target, source = rng.sample(range(count), 2)
                    before = live[target].copy()
                    other = live[source].copy()
                    after = before ^ other
                    operations.append({
                        "operation": "ADD_ROW_XOR",
                        "target_row": target,
                        "source_row": source,
                        "before": row(before),
                        "source": row(other),
                        "after": row(after),
                    })
                    live[target] = after
            with self.subTest(case=case):
                original = boundary_path_candidates_from_g5(initial, operations)
                native = boundary_path_candidates_from_g5_rust(initial, operations)
                self.assertEqual(native, original)
                self.assertEqual(native["status"], "DIAGNOSTIC_ONLY")
                independent_candidate_audit(initial, operations, native)

    def test_100_planted_simple_paths_and_reconstruction(self):
        for length in range(4, 24):
            for variant in range(5):
                labels = [i*5 + 1 + variant for i in range(length+1)]
                initial = [row((a,b)) for a,b in zip(labels, labels[1:])]
                initial.append(row((300+variant, 350+variant)))
                live = [set(r["coefficients"]) for r in initial]
                ops = []
                for source in range(1, length):
                    before = live[0].copy()
                    other = live[source].copy()
                    after = before ^ other
                    ops.append({
                        "operation": "ADD_ROW_XOR", "target_row": 0,
                        "source_row": source, "before": row(before),
                        "source": row(other), "after": row(after),
                    })
                    live[0] = after
                with self.subTest(length=length, variant=variant):
                    a = boundary_path_candidates_from_g5(initial, ops)
                    b = boundary_path_candidates_from_g5_rust(initial, ops)
                    self.assertEqual(a, b)
                    self.assertTrue(b["candidates"])
                    independent_candidate_audit(initial, ops, b)

    def test_tampered_replay_and_invalid_index_fail_closed(self):
        initial = [row((1,2)), row((2,3)), row((4,5))]
        valid = {
            "operation": "ADD_ROW_XOR", "target_row": 0, "source_row": 1,
            "before": row((1,2)), "source": row((2,3)), "after": row((1,3)),
        }
        invalid = [
            dict(valid, after=row((1,2))),
            dict(valid, source=row((4,5))),
            dict(valid, target_row=True),
            dict(valid, target_row=8),
            dict(valid, source_row=0),
            {"operation": "SWAP_ROWS", "row_a": 0, "row_b": 1,
             "rows_after": [row((1,2)), row((2,3)), row((4,5))]},
            {"operation": "NOT_G5"},
        ]
        for operation in invalid:
            with self.subTest(operation=operation):
                for func in (boundary_path_candidates_from_g5,
                             boundary_path_candidates_from_g5_rust):
                    with self.assertRaises(ValueError):
                        func(initial, [operation])
        for func in (boundary_path_candidates_from_g5,
                     boundary_path_candidates_from_g5_rust):
            with self.assertRaises(ValueError):
                func([row((1,1))], [])


if __name__ == "__main__":
    unittest.main()
