"""Offline checks for exact assumption-based syndrome queries and conflict cubes."""
import unittest

from scripts.experiment_satlib_incremental_syndrome_oracle import (
    add_forbidden_pattern, add_indexed_pattern, assumptions_for_syndrome,
    benchmark, forbidden, indexed_forbidden, make_syndrome_oracle,
    unsat_clause_pattern,
)


class IncrementalSyndromeOracleTests(unittest.TestCase):
    def test_native_xor_indicator_assumptions_and_conflict_direction(self):
        split = {"boundary": (), "right_vars": (2,), "right_clauses": [(2,)],
                 "right_xors": []}
        solver, ids = make_syndrome_oracle(split, "right", 0,
                                           [((2,), 0)], nvars=5)
        unsat_assumptions = assumptions_for_syndrome(ids, 0)
        sat, _ = solver.solve(assumptions=unsat_assumptions)
        self.assertFalse(sat)
        clause = solver.get_conflict()
        pattern = unsat_clause_pattern(clause, unsat_assumptions, ids)
        self.assertIsNotNone(pattern)
        self.assertTrue(forbidden([pattern], 0))
        self.assertFalse(forbidden([pattern], 1))
        sat, model = solver.solve(assumptions=assumptions_for_syndrome(ids, 1))
        self.assertTrue(sat)
        self.assertTrue(model[2])

    def test_core_cache_subsumption_and_fail_closed_wrong_sign(self):
        ids = (6, 7, 8)
        assumptions = (-6, 7, -8)
        clause = [6, -7]  # Falsified under these assumptions; 8 is irrelevant.
        pattern = unsat_clause_pattern(clause, assumptions, ids)
        self.assertEqual(pattern, (3, 2))
        self.assertTrue(forbidden([pattern], 2))
        self.assertTrue(forbidden([pattern], 6))
        self.assertFalse(forbidden([pattern], 3))
        self.assertIsNone(unsat_clause_pattern([-6], assumptions, ids))
        patterns = []
        self.assertTrue(add_forbidden_pattern(patterns, (7, 2)))
        self.assertTrue(add_forbidden_pattern(patterns, (3, 2)))
        self.assertEqual(patterns, [(3, 2)])
        self.assertFalse(add_forbidden_pattern(patterns, (7, 2)))

    def test_holdout_locked_before_fetch(self):
        with self.assertRaises(ValueError):
            benchmark("par32-2-c.cnf.Z")

    def test_indexed_cache_matches_exact_cylinder_union(self):
        patterns = [(1, 0), (3, 2), (7, 1), (5, 4), (3, 2)]
        index = {}
        for pattern in patterns:
            add_indexed_pattern(index, pattern)
        self.assertEqual(sum(map(len, index.values())), 4)
        for signature in range(8):
            self.assertEqual(indexed_forbidden(index, signature),
                             forbidden(patterns, signature))


if __name__ == "__main__":
    unittest.main()
