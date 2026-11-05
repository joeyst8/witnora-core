"""Exhaustive SAT checks for speculative two-step lookahead pivots."""
import random
import unittest
from itertools import product

from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.lookahead_pivot_prototype import (
    elimination_options, two_ply_pivot,
)


def brute_sat(formula):
    return any(formula_satisfied(formula, dict(zip(formula.variables, values)))
               for values in product((False, True), repeat=formula.num_vars))


class LookaheadPivotTests(unittest.TestCase):
    def test_random_bounded_transitions_preserve_sat(self):
        rng = random.Random(63063)
        for _ in range(80):
            rows = []
            for _ in range(rng.randint(1, 14)):
                chosen = rng.sample(range(1, 7), rng.randint(1, 3))
                rows.append([v if rng.getrandbits(1) else -v for v in chosen])
            source = CNFFormula.from_raw_clauses(rows)
            truth = brute_sat(source)
            for _, candidate in elimination_options(source):
                self.assertEqual(truth, brute_sat(candidate))
            self.assertEqual(truth, brute_sat(two_ply_pivot(source)))

    def test_deterministic_and_bounded(self):
        source = CNFFormula.from_raw_clauses([
            [1, 2], [-1, 3], [1, -3], [-2, 4], [2, -4], [-4, 5],
        ])
        a = two_ply_pivot(source)
        self.assertEqual(a, two_ply_pivot(source))
        self.assertGreaterEqual(a.num_vars, source.num_vars - 2)

    def test_invalid_configuration_rejected(self):
        with self.assertRaises(ValueError):
            two_ply_pivot(CNFFormula(), beam_width=0)
        with self.assertRaises(ValueError):
            two_ply_pivot(CNFFormula(), growth_budget=-1)


if __name__ == "__main__":
    unittest.main()
