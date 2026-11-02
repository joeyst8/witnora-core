"""Independent truth and backtracking checks for watched vs scanned BCP."""
import unittest
from random import Random

from pysat.solvers import Minisat22
from witnora_core.cnf import CNFFormula
from scripts.experiment_minisat_watch_reverse_engineering import TrailDPLL, benchmark


class WatchedPropagationTests(unittest.TestCase):
    def check_case(self, clauses):
        f = CNFFormula.from_raw_clauses(clauses)
        normalized = f.to_clause_lists()
        with Minisat22(bootstrap_with=normalized) as oracle:
            truth = oracle.solve()
        baseline = TrailDPLL(normalized, watched=False)
        watched = TrailDPLL(normalized, watched=True)
        self.assertEqual(baseline.run(), truth)
        self.assertEqual(watched.run(), truth)
        self.assertEqual(baseline.stats["decisions"], watched.stats["decisions"])

    def test_handcrafted_watcher_moves_and_undo(self):
        fixtures = [
            [], [()], [(1,), (-1,)], [(1, 2, 3), (-1,), (-2,)],
            [(1, 2, 3), (-1, -2), (-1, -3), (-2, -3)],
            [(1, 2, 3), (-1, 2, -3), (1, -2, 3), (-1, -2, -3)],
            [(1, 2, 3, 4), (-1, 5), (-2, 5), (-3, 5), (-4, 5), (-5,)],
            [(1, 2), (-1, 2), (1, -2), (-1, -2)],
        ]
        for clauses in fixtures:
            with self.subTest(clauses=clauses):
                self.check_case(clauses)

    def test_random_adversarial_cnf(self):
        for seed in range(350):
            rng = Random(2026611 + seed)
            n = rng.randrange(3, 13)
            clauses = []
            for _ in range(rng.randrange(3, n * 6)):
                support = rng.sample(range(1, n + 1), rng.randrange(1, min(n, 6) + 1))
                clauses.append(tuple(v if rng.randrange(2) else -v for v in support))
            self.check_case(clauses)

    def test_benchmark_smoke(self):
        result = benchmark(seeds=2, repeats=2)
        self.assertEqual(result["summary"]["cases"], 20)
        self.assertTrue(result["summary"]["truth_agreement"])
        self.assertTrue(result["summary"]["identical_search_decisions"])
        self.assertLess(result["summary"]["watch_clause_visits"],
                        result["summary"]["scan_clause_visits"])


if __name__ == "__main__":
    unittest.main()
