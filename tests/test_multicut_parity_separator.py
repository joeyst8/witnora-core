"""Planted minimal 2/3 cuts, and exactness/negative controls."""
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.multicut_parity_separator import bounded_parity_separators
from witnora_core.xor import canonical_xor_cnf_clauses


def pair(shared):
    k = len(shared)
    left = tuple(range(1, 3)) + shared
    right = shared + tuple(range(10, 12))
    return CNFFormula.from_raw_clauses(
        canonical_xor_cnf_clauses(left, 0)
        | canonical_xor_cnf_clauses(right, 1))


class MulticutParitySeparatorTests(unittest.TestCase):
    def test_minimal_two_variable_bridge(self):
        formula = pair((3, 4))
        result = bounded_parity_separators(formula)
        self.assertEqual(result["smallest_cut_size"], 2)
        self.assertEqual(result["candidate_cuts"][0]["variables"], [3, 4])
        self.assertFalse(result["full_cnf_separation_verified"])

    def test_minimal_three_variable_bridge(self):
        formula = pair((3, 4, 5))
        result = bounded_parity_separators(formula)
        self.assertEqual(result["smallest_cut_size"], 3)
        self.assertEqual(result["candidate_cuts"][0]["variables"], [3, 4, 5])

    def test_negative_disjoint_and_incomplete(self):
        disconnected = CNFFormula.from_raw_clauses(
            canonical_xor_cnf_clauses((1, 2, 3), 0)
            | canonical_xor_cnf_clauses((4, 5, 6), 1))
        self.assertEqual(bounded_parity_separators(disconnected)["candidate_count"], 0)
        source = pair((3, 4))
        reduced = CNFFormula(source.clauses[:-1])
        self.assertEqual(bounded_parity_separators(reduced)["candidate_count"], 0)

    def test_deterministic_bounded_and_fail_closed(self):
        source = pair((3, 4))
        self.assertEqual(bounded_parity_separators(source),
                         bounded_parity_separators(source))
        self.assertLessEqual(bounded_parity_separators(source, max_trials=1)["trials"], 1)
        with self.assertRaises(ValueError):
            bounded_parity_separators(source, max_cut=4)


if __name__ == "__main__":
    unittest.main()
