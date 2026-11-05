"""Independent exhaustive regression for experimental SAT transformations."""
import random
import unittest
from itertools import product

from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.experimental_operator_search import (
    OPERATORS, TRANSFORMS, RESEARCH_STATUS, explore_operators,
)


def brute_sat(formula):
    variables = formula.variables
    return any(
        formula_satisfied(formula, dict(zip(variables, bits)))
        for bits in product((False, True), repeat=len(variables))
    )


class ExperimentalOperatorSearchTest(unittest.TestCase):
    def test_each_operator_matches_exhaustive_sat_on_random_cnf(self):
        rng = random.Random(630630)
        for _ in range(120):
            rows = []
            for _ in range(rng.randrange(1, 15)):
                width = rng.randint(1, 3)
                variables = rng.sample(range(1, 6), width)
                rows.append([v if rng.getrandbits(1) else -v for v in variables])
            original = CNFFormula.from_raw_clauses(rows)
            truth = brute_sat(original)
            for name in OPERATORS:
                transformed = TRANSFORMS[name](original)
                self.assertEqual(
                    brute_sat(transformed), truth,
                    f"{name} changed satisfiability of {rows}",
                )
            for hypothesis in explore_operators(original, depth=3, beam_width=12):
                self.assertEqual(brute_sat(hypothesis.formula), truth)

    def test_reproducible_and_never_promoted(self):
        formula = CNFFormula.from_raw_clauses([
            [1, 2], [-1, -2], [2, 3], [-2, -3], [3, 4, 5],
        ])
        left = [h.record(formula) for h in explore_operators(formula)]
        right = [h.record(formula) for h in explore_operators(formula)]
        self.assertEqual(left, right)
        self.assertTrue(left)
        for record in left:
            self.assertEqual(record["status"], RESEARCH_STATUS)
            self.assertFalse(record["lean_verified"])
            self.assertFalse(record["promoted"])
            self.assertFalse(record["novelty_verified"])
            self.assertFalse(record["performance_advantage_verified"])

    def test_bounded_search_limits(self):
        with self.assertRaises(ValueError):
            explore_operators(CNFFormula(), depth=0)
        with self.assertRaises(ValueError):
            explore_operators(CNFFormula(), beam_width=0)


if __name__ == "__main__":
    unittest.main()
