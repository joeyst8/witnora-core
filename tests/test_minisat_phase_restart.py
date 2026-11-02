"""Controlled phase-saving/restarter ablation with independent oracle audit."""
import unittest
from random import Random

from pysat.solvers import Minisat22

from scripts.experiment_minisat_phase_restart import (
    ActivityPhaseRestart, MODES, benchmark, make_solver,
)
from scripts.experiment_minisat_first_uip import pigeonhole


class PhaseRestartTests(unittest.TestCase):
    def test_saved_negative_polarity_survives_backjump(self):
        solver = ActivityPhaseRestart([(1, -2)], phase_save=True, restarts=False)
        solver.trail_lim.append(0)
        self.assertTrue(solver.enqueue(-1))
        solver.backjump(0)
        self.assertEqual(solver.branch_literal(1), -1)
        self.assertEqual(solver.stats["saved_negative_phases"], 1)

    def test_bad_restart_interval_rejected(self):
        with self.assertRaises(ValueError):
            ActivityPhaseRestart([(1,)], first_restart=0)

    def test_random_complete_answers_and_all_learned_entailment(self):
        for seed in range(120):
            rng = Random(6291 + seed)
            n = rng.randrange(4, 14)
            clauses = []
            for _ in range(rng.randrange(n, n * 6)):
                support = rng.sample(range(1, n + 1), rng.randrange(1, min(n, 5) + 1))
                clauses.append(tuple(v if rng.randrange(2) else -v for v in support))
            with Minisat22(bootstrap_with=clauses) as oracle:
                truth = oracle.solve()
                for mode in MODES:
                    solver = make_solver(clauses, mode)
                    result = solver.solve(conflict_budget=2000)
                    self.assertEqual(result, truth, (seed, mode))
                    for learned in solver.learned:
                        self.assertFalse(oracle.solve(assumptions=[-lit for lit in learned]),
                                         (seed, mode, learned))

    def test_forced_restarts_preserve_correctness(self):
        for holes in (3, 4, 5):
            cnf = pigeonhole(holes + 1, holes)
            solver = ActivityPhaseRestart(cnf, phase_save=True, restarts=True,
                                          first_restart=1)
            self.assertFalse(solver.solve(conflict_budget=2000))
            self.assertGreater(solver.stats["restarts"], 0)
            with Minisat22(bootstrap_with=cnf) as oracle:
                for learned in solver.learned:
                    self.assertFalse(oracle.solve(assumptions=[-lit for lit in learned]))

    def test_budget_exhaustion_is_unknown(self):
        cnf = pigeonhole(8, 7)
        for mode in MODES:
            solver = make_solver(cnf, mode)
            self.assertIsNone(solver.solve(conflict_budget=2), mode)

    def test_benchmark_smoke(self):
        result = benchmark(seeds=2, repeats=1, conflict_budget=2000)
        self.assertEqual(result["summary"]["cases"], 27)
        self.assertEqual(result["summary"]["completed_answer_disagreements"], 0)


if __name__ == "__main__":
    unittest.main()
