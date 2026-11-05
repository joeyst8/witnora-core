"""Counterexample shrinking and structural elimination policy tests."""
import random
import unittest
from itertools import product

from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.operator_counterexamples import (
    interaction_gain, minimize_counterexample, apply_sequence,
)
from witnora_core.structural_operator_invention import (
    POLICIES, eliminate_with_policy, graph_invariants,
)


def brute_sat(formula):
    return any(
        formula_satisfied(formula, dict(zip(formula.variables, values)))
        for values in product((False, True), repeat=formula.num_vars)
    )


class StructureGuidedOperatorTests(unittest.TestCase):
    def test_all_structural_elimination_policies_are_satequivalent(self):
        rng = random.Random(6314)
        for _ in range(100):
            rows = []
            for _ in range(rng.randint(1, 14)):
                variables = rng.sample(range(1, 7), rng.randint(1, 3))
                rows.append([v if rng.getrandbits(1) else -v for v in variables])
            original = CNFFormula.from_raw_clauses(rows)
            for name in POLICIES:
                candidate = eliminate_with_policy(original, name)
                self.assertEqual(brute_sat(candidate), brute_sat(original))

    def test_graph_invariants_are_deterministic(self):
        formula = CNFFormula.from_raw_clauses([[1, 2, 3], [-1, 2], [2, 4]])
        self.assertEqual(graph_invariants(formula), graph_invariants(formula))
        self.assertEqual(graph_invariants(formula)["degree"][2], 3)

    def test_minimizer_produces_a_smaller_reproducer(self):
        formula = CNFFormula.from_raw_clauses([[1], [2], [3], [4], [5]])
        counterexample = minimize_counterexample(
            formula, lambda f: f.num_clauses >= 3,
            min_clauses=3, min_variables=3,
        )
        self.assertEqual(counterexample.num_clauses, 3)
        self.assertEqual(counterexample.num_vars, 3)

    def test_nonfailing_input_refused(self):
        with self.assertRaises(ValueError):
            minimize_counterexample(CNFFormula.from_raw_clauses([[1]]),
                                    lambda f: f.num_clauses > 2)

    def test_unknown_strategy_refused(self):
        with self.assertRaises(ValueError):
            apply_sequence(CNFFormula(), ("invented_unverified_name",))


if __name__ == "__main__":
    unittest.main()
