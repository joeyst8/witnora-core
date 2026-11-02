"""Independent semantic check of learned clauses and CDCL answers."""
import unittest
from random import Random

from pysat.solvers import Minisat22

from scripts.experiment_minisat_first_uip import FirstUIP, benchmark, pigeonhole
from scripts.experiment_minisat_watch_reverse_engineering import TrailDPLL


class FirstUIPTests(unittest.TestCase):
    def check_formula(self, clauses):
        with Minisat22(bootstrap_with=clauses) as oracle:
            expected = oracle.solve()
            solver = FirstUIP(clauses)
            self.assertEqual(solver.solve(), expected)
            for learned in solver.learned:
                # Independent oracle: original CNF entails learned clause C
                # iff original CNF and the negation of C are UNSAT.
                self.assertFalse(oracle.solve(assumptions=[-l for l in learned]),
                                 (clauses, learned))
        baseline = TrailDPLL(clauses, watched=True)
        self.assertEqual(baseline.run(), expected)

    def test_pigeonhole_and_adversarial(self):
        for holes in (2, 3, 4, 5, 6, 7):
            with self.subTest(holes=holes):
                self.check_formula(pigeonhole(holes + 1, holes))
        self.check_formula([(1, 2), (-1, 2), (1, -2), (-1, -2)])
        self.check_formula([(1,), (-1,)])
        self.check_formula([()])
        self.check_formula([])

    def test_random_against_independent_oracle_and_entailment(self):
        for seed in range(250):
            rng = Random(11207 + seed)
            n = rng.randrange(3, 13)
            clauses = []
            for _ in range(rng.randrange(4, n * 6)):
                support = rng.sample(range(1, n + 1), rng.randrange(1, min(5, n) + 1))
                clauses.append(tuple(v if rng.randrange(2) else -v for v in support))
            with self.subTest(seed=seed):
                self.check_formula(clauses)

    def test_matched_benchmark_smoke(self):
        result = benchmark(seeds=2, repeats=2)
        self.assertEqual(result["summary"]["cases"], 25)
        self.assertTrue(result["summary"]["all_answers_agree"])
        self.assertGreater(result["summary"]["learned_clauses"], 0)


if __name__ == "__main__":
    unittest.main()
