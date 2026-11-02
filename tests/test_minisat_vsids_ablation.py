"""VSIDS-style activity ablation: bounded correctness and learned-clause audit."""
import unittest
from random import Random

from pysat.solvers import Minisat22

from scripts.experiment_minisat_vsids_ablation import (
    ActivityFirstUIP, benchmark, random_near_transition,
)
from scripts.experiment_minisat_first_uip import FirstUIP, pigeonhole


class ActivityAblationTests(unittest.TestCase):
    def test_invalid_decay_rejected(self):
        for decay in (-1, 0, 1, 2):
            with self.assertRaises(ValueError):
                ActivityFirstUIP([(1,)], decay=decay)

    def test_randomized_semantic_audit(self):
        for seed in range(180):
            rng = Random(711277 + seed)
            n = rng.randrange(4, 14)
            clauses = []
            for _ in range(rng.randrange(n, n * 6)):
                support = rng.sample(range(1, n + 1), rng.randrange(1, min(4, n) + 1))
                clauses.append(tuple(v if rng.randrange(2) else -v for v in support))
            with Minisat22(bootstrap_with=clauses) as oracle:
                truth = oracle.solve()
                fixed = FirstUIP(clauses)
                activity = ActivityFirstUIP(clauses)
                self.assertEqual(fixed.solve(), truth)
                self.assertEqual(activity.solve(conflict_budget=2000), truth)
                for learned in activity.learned:
                    self.assertFalse(oracle.solve(assumptions=[-lit for lit in learned]),
                                     (seed, learned))

    def test_bound_is_unknown_not_unsat(self):
        hard = pigeonhole(8, 7)
        solver = ActivityFirstUIP(hard)
        self.assertIsNone(solver.solve(conflict_budget=2))
        self.assertEqual(solver.stats["budget_exhausted"], 1)
        with Minisat22(bootstrap_with=hard) as oracle:
            self.assertFalse(oracle.solve())
            for learned in solver.learned:
                self.assertFalse(oracle.solve(assumptions=[-lit for lit in learned]))

    def test_ood_transition_controls(self):
        for seed in range(30):
            f = random_near_transition(1000 + seed)
            clauses = f.to_clause_lists()
            with Minisat22(bootstrap_with=clauses) as oracle:
                expected = oracle.solve()
            result = ActivityFirstUIP(clauses).solve(conflict_budget=2000)
            self.assertEqual(result, expected)

    def test_benchmark_smoke(self):
        result = benchmark(seeds=2, repeats=2, conflict_budget=2000)
        self.assertEqual(result["summary"]["cases"], 27)
        self.assertTrue(result["summary"]["all_completed_answers_agree"])


if __name__ == "__main__":
    unittest.main()
