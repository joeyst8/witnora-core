"""Finite SAT differential and gate-selection tests."""
import random
import unittest
from itertools import product

from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.experimental_operator_search import bounded_elimination
from witnora_core.selective_lookahead_prototype import cheap_pivot_features, selective_pivot


def brute_sat(formula):
    return any(formula_satisfied(formula, dict(zip(formula.variables, assignment)))
               for assignment in product((False, True), repeat=formula.num_vars))


class SelectiveLookaheadTests(unittest.TestCase):
    def test_random_equivalence_and_determinism(self):
        rng = random.Random(74063)
        for _ in range(100):
            rows = []
            for _ in range(rng.randint(1, 14)):
                chosen = rng.sample(range(1, 7), rng.randint(1, 3))
                rows.append([v if rng.getrandbits(1) else -v for v in chosen])
            original = CNFFormula.from_raw_clauses(rows)
            result, metadata = selective_pivot(original)
            self.assertEqual(brute_sat(original), brute_sat(result))
            self.assertEqual((result, metadata), selective_pivot(original))
            self.assertFalse(metadata["trusted"])
            self.assertFalse(metadata["promoted"])
            self.assertLessEqual(metadata["expanded"], 24)

    def test_skip_is_identical_to_greedy(self):
        source = CNFFormula.from_raw_clauses([[1, 2], [-1, 3], [-2, 4]])
        result, metadata = selective_pivot(source, min_mixed_pivots=10)
        self.assertEqual(metadata["mode"], "greedy")
        self.assertEqual(result, bounded_elimination(bounded_elimination(source)))
        self.assertEqual(cheap_pivot_features(source)["variables"], 4)

    def test_invalid_budget_rejected(self):
        with self.assertRaises(ValueError):
            selective_pivot(CNFFormula(), expansion_budget=0)


if __name__ == "__main__":
    unittest.main()
