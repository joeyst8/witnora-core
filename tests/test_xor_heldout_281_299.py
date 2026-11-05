"""R-281–R-299: independent exact-cycle oracle and held-out proof checks."""

from __future__ import annotations

import os
import unittest

from scripts.benchmark_xor_heldout_281_299 import (
    exhaustive_shortest_odd_cycle, run_heldout,
)
from scripts.benchmark_xor_cycle_frontier import (
    cycle_case, measure_cycle, shortest_odd_parity_cycle,
)
from scripts.benchmark_xor_frontier import exhaustive_sat
from witnora_core.drat_trim import find_drat_trim
from witnora_core.xor import XorEquation


class XorHeldoutOptimalityTests(unittest.TestCase):
    def assert_width(self, n):
        formula, equations, _, _, _ = cycle_case(n, chords=min(n - 3, 3), seed=281000+n)
        shortest = shortest_odd_parity_cycle(equations)
        independent = exhaustive_shortest_odd_cycle(equations)
        self.assertIsNotNone(shortest)
        self.assertEqual(len(shortest), independent)
        self.assertFalse(exhaustive_sat(formula))

    def test_r281_three_vertices_exact_cycle(self): self.assert_width(3)
    def test_r282_four_vertices_exact_cycle(self): self.assert_width(4)
    def test_r283_five_vertices_exact_cycle(self): self.assert_width(5)
    def test_r284_six_vertices_exact_cycle(self): self.assert_width(6)
    def test_r285_seven_vertices_exact_cycle(self): self.assert_width(7)
    def test_r286_eight_vertices_exact_cycle(self): self.assert_width(8)

    def test_r287_heldout_sample_count(self):
        self.assertEqual(run_heldout(samples=72)["sample_count"], 72)

    def test_r288_exhaustive_edge_cap_fails_closed(self):
        equations = [XorEquation([i, i+1], 0) for i in range(1, 15)]
        with self.assertRaisesRegex(ValueError, "edge cap"):
            exhaustive_shortest_odd_cycle(equations)

    def test_r289_nonbinary_xor_rejected_by_witness_oracle(self):
        with self.assertRaisesRegex(ValueError, "binary"):
            exhaustive_shortest_odd_cycle([XorEquation([1], 0)])
        with self.assertRaisesRegex(ValueError, "binary"):
            shortest_odd_parity_cycle([XorEquation([1], 0)])

    def test_r290_heldout_shortest_cycle_optimality(self):
        rows = run_heldout(samples=72)["records"]
        self.assertTrue(all(row["shortest_odd_cycle"] == row["brute_force_odd_cycle"]
                            for row in rows))

    def test_r291_reproducibility_of_unseen_seeds(self):
        self.assertEqual(run_heldout(samples=24), run_heldout(samples=24))

    def test_r292_frozen_improvement_count_without_regression(self):
        result = run_heldout(samples=72)
        self.assertEqual(result["strict_witness_improvements"], 16)
        self.assertTrue(all(row["witness_proof_clauses"] <= row["full_proof_clauses"]
                            for row in result["records"]))

    def test_r293_planted_sat_controls_count(self):
        self.assertEqual(run_heldout(samples=72)["sat_control_count"], 24)

    def test_r294_true_sat_parity_graph_has_no_witness(self):
        formula, equations, _, _, _ = cycle_case(8, chords=4,
            seed=294, contradictory=False)
        self.assertTrue(exhaustive_sat(formula))
        self.assertIsNone(exhaustive_shortest_odd_cycle(equations))
        self.assertIsNone(shortest_odd_parity_cycle(equations))

    def test_r295_sparse_label_shortest_cycle_invariant(self):
        first = cycle_case(8, chords=4, seed=295)
        second = cycle_case(8, chords=4, seed=295, variable_gap=100)
        self.assertEqual(len(shortest_odd_parity_cycle(first[1])),
                         len(shortest_odd_parity_cycle(second[1])))
        self.assertEqual(exhaustive_shortest_odd_cycle(first[1]),
                         exhaustive_shortest_odd_cycle(second[1]))

    def test_r296_original_clause_order_keeps_evidence(self):
        self.assertEqual(measure_cycle(8, chords=4, seed=296),
                         measure_cycle(8, chords=4, seed=296, reverse_clauses=True))

    def test_r297_no_checker_no_external_claim(self):
        result = run_heldout(samples=12)
        self.assertFalse(result["external_drat_verification_performed"])
        self.assertTrue(all(not row["external_drat_verified"] for row in result["records"]))

    def test_r298_invalid_checker_cannot_be_skipped_silently(self):
        with self.assertRaisesRegex(ValueError, "unavailable"):
            run_heldout(samples=12, external_checker="/absent/drat-trim")

    def test_r299_different_heldout_seed_windows_remain_covered(self):
        a = run_heldout(samples=24)
        b = run_heldout(samples=72)
        self.assertEqual(a["records"], b["records"][:24])
        self.assertEqual(b["sample_count"], 72)


@unittest.skipUnless(find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM")),
                     "external drat-trim unavailable")
class XorHeldoutExternalTests(unittest.TestCase):
    def test_r281_r299_independent_external_checker_on_heldout(self):
        result = run_heldout(samples=72,
            external_checker=find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM")))
        self.assertTrue(all(row["external_drat_verified"] for row in result["records"]))


class XorHeldoutNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("native extension absent; CI builds it")

    def test_r281_r299_native_heldout_differential(self):
        result = run_heldout(samples=72, compare_rust=True)
        self.assertTrue(result["native_differential"])


if __name__ == "__main__":
    unittest.main()
