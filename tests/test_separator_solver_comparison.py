"""Regression tests for exact decomposition solving and controlled comparisons."""
import unittest

from scripts.benchmark_separator_decomposition import (
    benchmark, components, solve_dpll, solve_with_cut,
)


class SeparatorSolverComparisonTests(unittest.TestCase):
    def test_dpll_sat_and_unsat(self):
        self.assertTrue(solve_dpll([[1, 2], [-1, 2]], {"nodes": 0}))
        self.assertFalse(solve_dpll([[1], [-1]], {"nodes": 0}))

    def test_components_separate_after_conditioning(self):
        groups = components([[1, 2], [-1, 2], [3, 4], [-3, 4]])
        self.assertEqual(len(groups), 2)

    def test_cut_solver_agrees_for_sat_and_unsat(self):
        for rows in (
            [[1, 2], [-1, 3], [2, 4], [-2, -4]],
            [[1], [-1], [2, 3]],
            [[1, 2], [-1, -2]],
        ):
            expected = solve_dpll(rows, {"nodes": 0})
            actual = solve_with_cut(rows, [1], {
                "nodes": 0, "boundary_assignments": 0})
            self.assertEqual(expected, actual)

    def test_blind_benchmark_answer_agreement(self):
        output = benchmark(seed_count=2)
        self.assertEqual(output["summary"]["total"], 14)
        self.assertEqual(output["summary"]["answers_agree"], 14)


if __name__ == "__main__":
    unittest.main()
