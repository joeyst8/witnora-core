"""Exhaustive finite checks for adaptive elimination, kept outside Lean."""
import random
import unittest
from itertools import product

from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.experimental_operator_search import bounded_elimination, structural_score
from witnora_core.adaptive_lookahead_prototype import adaptive_pivot


def sat(formula):
    return any(formula_satisfied(formula, dict(zip(formula.variables, values)))
               for values in product((False, True), repeat=formula.num_vars))


class AdaptiveLookaheadTests(unittest.TestCase):
    def test_random_sat_and_structural_guard(self):
        rng = random.Random(64063)
        for _ in range(100):
            rows = []
            for _ in range(rng.randint(1, 14)):
                chosen = rng.sample(range(1, 7), rng.randint(1, 3))
                rows.append([v if rng.getrandbits(1) else -v for v in chosen])
            source = CNFFormula.from_raw_clauses(rows)
            candidate, meta = adaptive_pivot(source)
            greedy = bounded_elimination(bounded_elimination(source))
            self.assertEqual(sat(source), sat(candidate))
            self.assertGreaterEqual(structural_score(source, candidate),
                                    structural_score(source, greedy))
            self.assertFalse(meta["trusted"])
            self.assertFalse(meta["promoted"])
            self.assertLessEqual(meta["expanded"], 48)

    def test_deterministic_and_validation(self):
        source = CNFFormula.from_raw_clauses(
            [[1, 2], [-1, 3], [1, -3], [-2, 4], [2, -4], [-4, 5]])
        self.assertEqual(adaptive_pivot(source), adaptive_pivot(source))
        for kwargs in ({"beam_width": 0}, {"expansion_budget": 0},
                       {"growth_budget": -1}, {"max_depth": 4}):
            with self.assertRaises(ValueError):
                adaptive_pivot(source, **kwargs)


if __name__ == "__main__":
    unittest.main()
