"""Independent false-UNSAT controls for bounded affine/CNF pair screening."""
import random
import unittest
from itertools import product

from scripts.experiment_affine_pair_conflict import (
    controlled_instance, run, screen_pairs, selective_screen_pairs,
)


def independent_sat(nvars, rows, clauses):
    for bits in product((0, 1), repeat=nvars):
        if all(sum(bits[i] for i in range(nvars) if mask & (1 << i)) % 2 == rhs
               for mask, rhs in rows) and all(
                   any((lit > 0) == bool(bits[abs(lit) - 1]) for lit in clause)
                   for clause in clauses):
            return True
    return False


class AffinePairConflictTests(unittest.TestCase):
    def test_zero_false_unsat_against_exhaustive_oracle(self):
        rng = random.Random(63127)
        for _ in range(220):
            nvars = rng.randrange(1, 8)
            rows = [(rng.randrange(1 << nvars), rng.randrange(2))
                    for _ in range(rng.randrange(0, 7))]
            clauses = []
            for _ in range(rng.randrange(0, 9)):
                variables = rng.sample(range(1, nvars + 1),
                                       rng.randrange(1, min(3, nvars) + 1))
                clauses.append(tuple(v if rng.randrange(2) else -v
                                     for v in variables))
            decision = screen_pairs(nvars, rows, clauses, max_pairs=20)
            selective = selective_screen_pairs(nvars, rows, clauses, max_pairs=20)
            for result in (decision, selective):
                if result["status"] == "UNSAT":
                    self.assertFalse(independent_sat(nvars, rows, clauses))

    def test_target_pair_requires_two_clauses(self):
        rows, clauses = controlled_instance(16, 0, "unsat_pair")
        self.assertTrue(independent_sat(2, rows[:1], []))
        for clause in clauses[:2]:
            self.assertTrue(independent_sat(2, rows[:1], [clause]))
        result = screen_pairs(16, rows, clauses, max_pairs=1)
        self.assertEqual(result["status"], "UNSAT")
        self.assertEqual(result["reason"], "PAIR_AFFINE_CONTRADICTION")
        self.assertEqual(result["source_indices"], [0, 1])
        selective = selective_screen_pairs(16, rows, clauses, max_pairs=1)
        self.assertEqual(selective["status"], "UNSAT")
        self.assertEqual(selective["reason"], "SELECTIVE_PAIR_CONTRADICTION")

    def test_sat_control_is_not_claimed_unsat(self):
        rows, clauses = controlled_instance(32, 0, "sat_control")
        self.assertEqual(screen_pairs(32, rows, clauses)["status"], "UNKNOWN")
        self.assertEqual(selective_screen_pairs(32, rows, clauses)["status"], "UNKNOWN")
        summary = run(seeds=2)["summary"]
        self.assertEqual(summary["targeted_pair_detected"], 4)
        self.assertEqual(summary["selective_targeted_detected"], 4)
        self.assertEqual(summary["sat_control_false_unsat"], 0)


if __name__ == "__main__":
    unittest.main()
