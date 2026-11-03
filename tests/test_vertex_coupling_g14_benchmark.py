"""Candidate counts and actual G14 recognition times for vertex coupling.

The benchmark uses canonical ternary XOR-CNF clauses x XOR y XOR z = 0.
No clause is contained in a candidate pair, avoiding a zero-variable C0
artifact that could be confused with a genuine graph separator.
"""

import json
import random
import statistics
import time
import unittest
from itertools import combinations

from tests.test_g5_pairwise_dense_bridge import regular_two_cut_edges
from tests.test_global_coupling_separator import graph_of, two_cut_oracle
from witnora_core.cnf import CNFFormula
from witnora_core.separator_affine_family_theorem import (
    SEPARATOR_AFFINE_FAMILY_RECOGNIZED,
    primal_graph,
    recognize_separator_affine_family,
)
from witnora_core.vertex_coupling_separator import (
    vertex_coupling_pairs,
    prioritized_vertex_pairs,
)
from witnora_core.xor import canonical_xor_cnf_clauses


def ternary_spoke_affine_formula(internal_count):
    selectors = (100, 101)
    clauses = [
        clause
        for internal in range(1, internal_count + 1)
        for clause in canonical_xor_cnf_clauses(
            (selectors[0], selectors[1], internal), 0
        )
    ]
    return CNFFormula.from_raw_clauses(clauses)


class VertexCouplingG14BenchmarkTest(unittest.TestCase):
    def test_graph_candidate_rank_against_lexicographic(self):
        rng = random.Random(630639)
        report = {}
        for k in (4, 5, 6, 7):
            n = 2 * k
            edges = regular_two_cut_edges(k)
            lex_rank = []
            for _ in range(48):
                mapping = dict(enumerate(rng.sample(range(1, 4096), n)))
                graph = graph_of(mapping.values(), [
                    (mapping[a], mapping[b]) for a, b in edges
                ])
                exact = two_cut_oracle(graph)
                lex = list(combinations(sorted(graph), 2))
                preferred = prioritized_vertex_pairs(graph)
                self.assertIn(preferred[0], exact)
                self.assertEqual(
                    {tuple(row["separator"]) for row in vertex_coupling_pairs(graph)["candidates"]},
                    exact,
                )
                lex_rank.append(next(i for i, pair in enumerate(lex, 1) if pair in exact))
            report[n] = {
                "trials": 48,
                "vertex_coupling_first_true_cut_rank": 1,
                "lex_first_true_cut_rank_mean": round(statistics.mean(lex_rank), 3),
                "lex_first_true_cut_rank_median": statistics.median(lex_rank),
                "lex_first_true_cut_rank_max": max(lex_rank),
            }
        print("VERTEX_COUPLING_GRAPH_RANK_BENCHMARK", json.dumps(report, sort_keys=True))

    def test_real_g14_high_label_ternary_xor_cnf(self):
        results = {}
        for count in (6, 8):
            formula = ternary_spoke_affine_formula(count)
            graph = primal_graph(formula)
            self.assertEqual(two_cut_oracle(graph), {(100, 101)})
            self.assertTrue(all(len(clause) == 3 for clause in formula.clauses))
            entry = {}
            for mode in ("vertex_coupling", "lexicographic"):
                begin = time.perf_counter()
                accepted = recognize_separator_affine_family(
                    formula, c=2, r=3, priority=mode
                )
                elapsed = time.perf_counter() - begin
                self.assertEqual(accepted["status"], SEPARATOR_AFFINE_FAMILY_RECOGNIZED)
                self.assertEqual(accepted["separator_variables"], [100, 101])
                self.assertTrue(accepted["trace"][-1]["accepted"])
                entry[mode] = {
                    "candidates_examined": accepted["candidates_examined"],
                    "elapsed_seconds": round(elapsed, 6),
                }
            n = len(graph)
            self.assertEqual(entry["vertex_coupling"]["candidates_examined"], n + 1)
            self.assertEqual(
                entry["lexicographic"]["candidates_examined"], n + n * (n - 1) // 2
            )
            results[n] = entry
        print("VERTEX_COUPLING_REAL_G14_BENCHMARK", json.dumps(results, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
