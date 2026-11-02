"""Fail-closed checks for the experimental cut-selection benchmark."""

import unittest

from research.pr119_separator_selection_benchmark import (
    cached_cut,
    exact_affine_candidate,
    measure,
    random_three_sat_control,
    relabel_formula,
    source_formula,
)


class SeparatorSelectionBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.formula = source_formula()

    def test_both_policies_find_real_exact_affine_cuts(self):
        first = cached_cut(self.formula, "cached_first", c=2, r=3)
        balanced = cached_cut(self.formula, "cached_balanced", c=2, r=3)
        self.assertEqual(first["cut"], [1, 38])
        self.assertEqual(balanced["cut"], [10, 29])
        self.assertEqual(balanced["graph_cuts"], 19)
        self.assertTrue(exact_affine_candidate(self.formula, (1, 38), 3))
        self.assertTrue(exact_affine_candidate(self.formula, (10, 29), 3))

    def test_balanced_policy_produces_a_rechecked_real_unsat_certificate(self):
        result = measure(self.formula, "test", "cached_balanced", c=2, r=3)
        self.assertEqual(result["status"], "UNSAT_CERTIFIED")
        self.assertEqual(result["component_sizes"], [29, 29])
        self.assertGreater(result["certificate_bytes"], 0)

    def test_relabel_does_not_destroy_bounded_graph_cuts(self):
        new_formula = relabel_formula(self.formula, 11)
        self.assertEqual(len(new_formula.clauses), 160)
        candidate = cached_cut(new_formula, "cached_balanced", c=2, r=3)
        self.assertEqual(candidate["graph_cuts"], 19)
        self.assertEqual(len(candidate["cut"]), 2)

    def test_negative_control_does_not_receive_a_spurious_separator(self):
        formula = random_three_sat_control(20261102)
        self.assertEqual(len(formula.clauses), 160)
        for policy in ("cached_first", "cached_balanced"):
            self.assertEqual(cached_cut(formula, policy, c=2, r=3)["cut"], [])


if __name__ == "__main__":
    unittest.main()
