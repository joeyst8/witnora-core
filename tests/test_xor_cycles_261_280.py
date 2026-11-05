"""R-261–R-280: structure-guided contradictory-cycle proof research."""

from __future__ import annotations

import os
import unittest

from scripts.benchmark_xor_cycle_frontier import (
    cycle_case, measure_cycle, run_cycles, shortest_odd_parity_cycle,
)
from scripts.benchmark_xor_frontier import exhaustive_sat
from witnora_core.drat_trim import find_drat_trim
from witnora_core.xor_drat import _row_trace_refutation, _sparse_xor_elimination_schedule
from witnora_core.cnf import CNFFormula


CONFIGS = ((3, 0), (4, 0), (5, 1), (6, 1), (8, 2),
           (10, 3), (12, 4), (16, 5), (20, 6), (40, 10))


class XorCycleResearchTests(unittest.TestCase):
    def assert_case(self, index):
        n, chords = CONFIGS[index]
        result = measure_cycle(n, chords=chords, seed=261000 + n)
        self.assertEqual(result["status"], "CANDIDATE_RUP_ACCEPTED")
        self.assertEqual(result["graph_cycle_rank"], chords + 1)
        self.assertEqual(result["shortest_inconsistent_cycle_edges"],
                         result["shortest_witness_edges"])
        self.assertGreater(result["witness_proof_clauses"], 0)

    def test_r261_triangle(self): self.assert_case(0)
    def test_r262_square(self): self.assert_case(1)
    def test_r263_five_vertex_chord(self): self.assert_case(2)
    def test_r264_six_vertex_chord(self): self.assert_case(3)
    def test_r265_eight_vertex_two_chords(self): self.assert_case(4)
    def test_r266_ten_vertex_three_chords(self): self.assert_case(5)
    def test_r267_twelve_vertex_four_chords(self): self.assert_case(6)
    def test_r268_sixteen_vertex_five_chords(self): self.assert_case(7)
    def test_r269_twenty_vertex_six_chords(self): self.assert_case(8)
    def test_r270_forty_vertex_ten_chords(self): self.assert_case(9)

    def test_r271_odd_parity_cycle_is_closed_and_inconsistent(self):
        formula, equations, _, _, _ = cycle_case(20, chords=6, seed=261020)
        indices = shortest_odd_parity_cycle(equations)
        parity = 0
        degree = {}
        for index in indices:
            equation = equations[index]
            parity ^= equation.rhs
            for v in equation.variables:
                degree[v] = degree.get(v, 0) + 1
        self.assertEqual(parity, 1)
        self.assertTrue(all(count % 2 == 0 for count in degree.values()))
        self.assertFalse(exhaustive_sat(CNFFormula([[1], [-1]])))  # oracle sanity

    def test_r272_independent_cycle_rank(self):
        for n, chords in CONFIGS:
            self.assertEqual(measure_cycle(n, chords=chords)["graph_cycle_rank"], chords + 1)

    def test_r273_full_original_cnf_source_accounting(self):
        for n, chords in CONFIGS:
            self.assertEqual(measure_cycle(n, chords=chords)["source_clauses"],
                             2 * (n + chords))

    def test_r274_shortest_witness_never_worse_on_frozen_suite(self):
        for row in run_cycles()["rows"]:
            self.assertLessEqual(row["witness_proof_clauses"], row["proof_clauses"])

    def test_r275_witness_reduces_frozen_40_vertex_proof(self):
        row = measure_cycle(40, chords=10, seed=261040)
        self.assertEqual((row["proof_clauses"],row["witness_proof_clauses"]), (67,21))

    def test_r276_witness_two_literals_per_cycle_edge_pattern(self):
        for row in run_cycles()["rows"]:
            self.assertEqual(row["witness_proof_clauses"],
                             2 * row["shortest_witness_edges"] - 1)

    def test_r277_consistent_sat_graph_has_no_odd_witness(self):
        formula, equations, _, _, _ = cycle_case(8, chords=2,
            seed=277, contradictory=False)
        self.assertTrue(exhaustive_sat(formula))
        self.assertIsNone(shortest_odd_parity_cycle(equations))
        self.assertEqual(measure_cycle(8, chords=2, seed=277,
                                     contradictory=False)["status"],
                         "ROW_OPERATION_TRACE_DID_NOT_DERIVE_EMPTY")

    def test_r278_sparse_relabel_still_finds_same_odd_cycle(self):
        baseline = measure_cycle(20, chords=6, seed=278)
        relabel = measure_cycle(20, chords=6, seed=278, variable_gap=73)
        self.assertEqual(baseline["shortest_witness_edges"], relabel["shortest_witness_edges"])
        self.assertEqual(baseline["witness_proof_clauses"], relabel["witness_proof_clauses"])

    def test_r279_source_clause_reordering_invariance(self):
        baseline = measure_cycle(20, chords=6, seed=279)
        reordered = measure_cycle(20, chords=6, seed=279, reverse_clauses=True)
        self.assertEqual(baseline, reordered)

    def test_r280_shortest_witness_rejects_missing_original_support(self):
        formula, equations, _, _, _ = cycle_case(8, chords=2, seed=280)
        indices = shortest_odd_parity_cycle(equations)
        witness = [equations[i] for i in indices]
        trace = _sparse_xor_elimination_schedule(witness)["row_operation_trace"]
        target = min(witness[0].source_clauses)
        reduced = CNFFormula(c for c in formula.to_clause_lists() if tuple(c) != target)
        proof, error, _ = _row_trace_refutation(reduced, witness, trace,
            max_proof_clauses=10000, max_proof_bytes=200000, timeout_seconds=None)
        self.assertIsNone(proof)
        self.assertEqual(error, "DETECTED_XOR_SOURCE_CLAUSE_MISSING_FROM_ORIGINAL")


@unittest.skipUnless(find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM")),
                     "external drat-trim required")
class XorCycleExternalTests(unittest.TestCase):
    def test_r261_r280_full_original_cnf_external_checker(self):
        result = run_cycles(external_checker=find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM")))
        self.assertTrue(all(row["external_drat_verified"] for row in result["rows"]))


class XorCycleNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("native extension absent; CI builds it")

    def test_r261_r280_native_vs_reference_for_full_and_compact_proofs(self):
        result = run_cycles(compare_rust=True)
        self.assertTrue(all(row["native_differential"] for row in result["rows"]))


if __name__ == "__main__":
    unittest.main()
