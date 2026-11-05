"""Independent assignment-oracle checks for unseen-problem generators."""
import unittest
from itertools import product

from witnora_core.cnf import formula_satisfied
from witnora_core.ood_sat_families import (
    graph_coloring, n_queens, out_of_distribution_cases,
    pigeonhole, random_planted_3cnf, tseitin_k4,
)


def brute_sat(formula):
    return any(
        formula_satisfied(formula, dict(zip(formula.variables, values)))
        for values in product((False, True), repeat=formula.num_vars)
    )


class UnseenFamilyTests(unittest.TestCase):
    def test_pigeonhole(self):
        self.assertFalse(brute_sat(pigeonhole(3, 2)))
        self.assertTrue(brute_sat(pigeonhole(2, 2)))

    def test_graph_coloring(self):
        self.assertFalse(brute_sat(graph_coloring(
            4, [(1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)], 3)))
        self.assertTrue(brute_sat(graph_coloring(
            3, [(1, 2), (2, 3)], 2)))

    def test_tseitin(self):
        self.assertTrue(brute_sat(tseitin_k4(contradictory=False)))
        self.assertFalse(brute_sat(tseitin_k4(contradictory=True)))

    def test_queens(self):
        self.assertFalse(brute_sat(n_queens(3)))
        self.assertTrue(brute_sat(n_queens(4)))

    def test_planted(self):
        self.assertTrue(brute_sat(random_planted_3cnf(7, 20, 101)))

    def test_reproducible_distinct_case_ids(self):
        a = out_of_distribution_cases(101)
        b = out_of_distribution_cases(101)
        self.assertEqual([x[1:] for x in a], [x[1:] for x in b])
        self.assertEqual(len(a), 10)
        self.assertEqual(len({x[1] for x in a}), 10)


if __name__ == "__main__":
    unittest.main()
