"""Finite truth checks of separator-conditioned exact SAT search."""
import random
import unittest
from itertools import product

from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.hidden_separator_challenge import make_hidden_separator
from witnora_core.separator_conditioned_solve import (
    primal_components, restrict_formula, solve_conditioned,
)


def brute_sat(formula):
    return any(formula_satisfied(formula, dict(zip(formula.variables, values)))
               for values in product((False, True), repeat=formula.num_vars))


class SeparatorConditionedSolveTests(unittest.TestCase):
    def test_controlled_full_cnf_cut_and_cross_obstruction(self):
        for width in (2, 3):
            for cross in (False, True):
                source, _ = make_hidden_separator(71, width=width, cross_noise=cross)
                result = solve_conditioned(source)
                self.assertEqual(result["mode"], "direct_fallback" if cross else "conditioned")
                self.assertFalse(result["promoted"])

    def test_small_random_truth(self):
        rng = random.Random(98071)
        for _ in range(40):
            rows = []
            for _ in range(rng.randint(1, 10)):
                chosen = rng.sample(range(1, 6), rng.randint(1, 3))
                rows.append([v if rng.getrandbits(1) else -v for v in chosen])
            source = CNFFormula.from_raw_clauses(rows)
            self.assertEqual(solve_conditioned(source)["satisfiable"], brute_sat(source))

    def test_restriction_and_graph(self):
        source = CNFFormula.from_raw_clauses([[1, 2], [-1, 3]])
        reduced = restrict_formula(source, {1: True})
        self.assertEqual(reduced.to_clause_lists(), [[3]])
        self.assertEqual(primal_components(source, (1,)), [(2,), (3,)])


if __name__ == "__main__":
    unittest.main()
