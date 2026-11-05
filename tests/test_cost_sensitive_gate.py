"""Guard threshold fitting and exact SAT preservation on finite examples."""
import random
import unittest
from itertools import product

from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.cost_sensitive_gate import (
    THRESHOLDS, choose_threshold, cost_sensitive_pivot,
)


def sat(f):
    return any(formula_satisfied(f, dict(zip(f.variables, values)))
               for values in product((False, True), repeat=f.num_vars))


class CostSensitiveGateTests(unittest.TestCase):
    def test_cost_penalty_can_prefer_greedy(self):
        observations = [{"mixed_pivots": 5, "variables": 6, "clauses": 10,
                         "adaptive_score": 8, "greedy_score": 4,
                         "adaptive_ms": 10, "greedy_ms": 1}]
        self.assertEqual(choose_threshold(observations, cost_weight=2)["threshold"],
                         1000000)
        self.assertEqual(choose_threshold(observations, cost_weight=0)["threshold"], 5)

    def test_finite_sat_truth_and_determinism(self):
        rng = random.Random(86063)
        for _ in range(80):
            rows = []
            for _ in range(rng.randint(1, 13)):
                chosen = rng.sample(range(1, 7), rng.randint(1, 3))
                rows.append([v if rng.getrandbits(1) else -v for v in chosen])
            original = CNFFormula.from_raw_clauses(rows)
            for threshold in (2, 5, 1000000):
                result, info = cost_sensitive_pivot(original, threshold=threshold)
                self.assertEqual(sat(original), sat(result))
                self.assertFalse(info["promoted"])
                self.assertEqual((result, info),
                                 cost_sensitive_pivot(original, threshold=threshold))

    def test_rejects_invalid_inputs(self):
        with self.assertRaises(ValueError):
            choose_threshold([])
        with self.assertRaises(ValueError):
            cost_sensitive_pivot(CNFFormula(), threshold=4)
        self.assertEqual(THRESHOLDS[-1], 1000000)


if __name__ == "__main__":
    unittest.main()
