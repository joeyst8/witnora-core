"""Fail-closed checks for second-stage unfamiliar-instance stress tests."""
import unittest

from scripts.benchmark_ood_larger import run
from witnora_core.ood_sat_families import larger_unseen_cases, tseitin_complete_graph
from tests.test_ood_sat_families import brute_sat


class LargerOODTests(unittest.TestCase):
    def test_larger_cases_are_deterministic_and_labelled(self):
        first = larger_unseen_cases(401)
        again = larger_unseen_cases(401)
        self.assertEqual(len(first), 8)
        self.assertEqual(len({case_id for _, case_id, _, _ in first}), 8)
        self.assertEqual([(f, c, x.formula_hash, truth)
                          for f, c, x, truth in first],
                         [(f, c, x.formula_hash, truth)
                          for f, c, x, truth in again])
        self.assertEqual(len({family for family, _, _, _ in first}), 5)
        self.assertTrue(all(isinstance(expected, bool)
                            for _, _, _, expected in first))

    def test_small_complete_graph_tseitin_has_expected_truth(self):
        self.assertTrue(brute_sat(tseitin_complete_graph(
            3, contradictory=False)))
        self.assertFalse(brute_sat(tseitin_complete_graph(
            3, contradictory=True)))
        with self.assertRaises(ValueError):
            tseitin_complete_graph(8, contradictory=False)

    def test_empty_screen_is_rejected(self):
        with self.assertRaises(ValueError):
            run([])


if __name__ == "__main__":
    unittest.main()
