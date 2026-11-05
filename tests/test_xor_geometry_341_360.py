"""R-341–R-360: matched CNF size/degree but different GF2 interaction ranks."""

from __future__ import annotations

import os
import unittest

from scripts.benchmark_xor_constraint_geometry import (
    geometry, measure_geometry, run_matched, support_rank,
)
from scripts.benchmark_xor_frontier import exhaustive_sat
from witnora_core.drat_trim import find_drat_trim


class XorMatchedGeometryTests(unittest.TestCase):
    def assert_pair(self, n):
        cycle = measure_geometry(n, "cycle")
        paired = measure_geometry(n, "parallel_pairs")
        for property_name in ("variables", "constraints", "clause_width",
                              "variable_degrees", "source_clauses"):
            self.assertEqual(cycle[property_name],paired[property_name])
        self.assertEqual(cycle["gf2_support_rank"],n-1)
        self.assertEqual(paired["gf2_support_rank"],n//2)
        self.assertGreater(cycle["proof_clauses"],paired["proof_clauses"])

    def test_r341_matched_n4(self): self.assert_pair(4)
    def test_r342_matched_n6(self): self.assert_pair(6)
    def test_r343_matched_n8(self): self.assert_pair(8)
    def test_r344_matched_n10(self): self.assert_pair(10)
    def test_r345_matched_n12(self): self.assert_pair(12)
    def test_r346_matched_n14(self): self.assert_pair(14)

    def test_r347_same_variable_count(self):
        for n in range(4,15,2):
            self.assertEqual(measure_geometry(n,"cycle")["variables"],n)
            self.assertEqual(measure_geometry(n,"parallel_pairs")["variables"],n)

    def test_r348_same_constraint_count(self):
        for n in range(4,15,2):
            self.assertEqual(measure_geometry(n,"cycle")["constraints"],n)
            self.assertEqual(measure_geometry(n,"parallel_pairs")["constraints"],n)

    def test_r349_same_variable_degree_profile(self):
        for row in run_matched()["results"]:
            self.assertEqual(row["variable_degrees"],[2]*row["n"])

    def test_r350_same_binary_xor_arity(self):
        self.assertTrue(all(row["clause_width"]==2 for row in run_matched()["results"]))

    def test_r351_exact_same_unique_cnf_source_clause_count(self):
        self.assertTrue(all(row["source_clauses"]==2*row["n"]
                            for row in run_matched()["results"]))

    def test_r352_cycle_minimum_inconsistent_rows_n(self):
        self.assertTrue(all(measure_geometry(n,"cycle")["minimum_inconsistent_rows"]==n
                            for n in range(4,15,2)))

    def test_r353_pairs_minimum_inconsistent_rows_two(self):
        self.assertTrue(all(measure_geometry(n,"parallel_pairs")
                            ["minimum_inconsistent_rows"]==2 for n in range(4,15,2)))

    def test_r354_cycle_rank_n_minus_one(self):
        for n in range(4,15,2):
            _, rows=geometry(n,"cycle")
            self.assertEqual(support_rank(rows),n-1)

    def test_r355_paired_component_rank_n_over_two(self):
        for n in range(4,15,2):
            _, rows=geometry(n,"parallel_pairs")
            self.assertEqual(support_rank(rows),n//2)

    def test_r356_cycle_reachable_syndrome_states(self):
        for n in range(4,15,2):
            self.assertEqual(measure_geometry(n,"cycle")["syndrome_reachable_states"],2**n)

    def test_r357_parallel_pairs_reachable_syndrome_states(self):
        for n in range(4,15,2):
            self.assertEqual(measure_geometry(n,"parallel_pairs")
                             ["syndrome_reachable_states"],2**(n//2+1))

    def test_r358_same_size_strong_state_space_divergence(self):
        left=measure_geometry(14,"cycle")
        right=measure_geometry(14,"parallel_pairs")
        self.assertEqual(left["syndrome_reachable_states"]//right["syndrome_reachable_states"],64)

    def test_r359_consistent_matched_graphs_have_sat_models(self):
        for n in (4,6,8):
            for family in ("cycle","parallel_pairs"):
                formula,_=geometry(n,family,contradictory=False)
                self.assertTrue(exhaustive_sat(formula))
                self.assertIsNone(measure_geometry(n,family,contradictory=False)
                                  ["minimum_inconsistent_rows"])

    def test_r360_bounded_matched_geometry_guard(self):
        for bad in (3,5,17,18):
            with self.assertRaisesRegex(ValueError,"even n"):
                geometry(bad,"cycle")


@unittest.skipUnless(find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM")),
                     "external drat-trim unavailable")
class XorGeometryExternalTests(unittest.TestCase):
    def test_r341_r360_independent_external_proof_acceptance(self):
        checker=find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM"))
        result=run_matched(external_checker=checker)
        self.assertTrue(all(row["external_drat_verified"] for row in result["results"]))


class XorGeometryNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("native Rust extension absent; CI provides it")

    def test_r341_r360_rust_python_matched_proof_comparisons(self):
        result=run_matched(compare_rust=True)
        self.assertTrue(all(row["native_differential"] for row in result["results"]))


if __name__=="__main__":
    unittest.main()
