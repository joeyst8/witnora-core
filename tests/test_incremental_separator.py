"""Cache correctness and exact-screen negative controls."""
import random
import unittest
from itertools import product

from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.hidden_separator_challenge import make_hidden_separator
from witnora_core.incremental_separator import (
    possible_two_xor_patterns, cached_full_cut, solve_incremental,
)


def brute_sat(formula):
    return any(formula_satisfied(formula, dict(zip(formula.variables, bits)))
               for bits in product((False, True), repeat=formula.num_vars))


class IncrementalSeparatorTests(unittest.TestCase):
    def test_cache_hit_and_cross_constraint_fail_closed(self):
        cached_full_cut.cache_clear()
        good, _ = make_hidden_separator(43, width=2, cross_noise=False)
        bad, _ = make_hidden_separator(43, width=2, cross_noise=True)
        self.assertTrue(possible_two_xor_patterns(good))
        self.assertIsNotNone(cached_full_cut(good))
        self.assertIsNone(cached_full_cut(bad))
        self.assertEqual(solve_incremental(good)["mode"], "conditioned")
        self.assertEqual(solve_incremental(bad)["mode"], "direct_fallback")
        before = cached_full_cut.cache_info().hits
        solve_incremental(good)
        self.assertGreater(cached_full_cut.cache_info().hits, before)

    def test_random_finite_truth(self):
        rng = random.Random(118071)
        for _ in range(60):
            clauses = []
            for _ in range(rng.randint(1, 12)):
                vs = rng.sample(range(1, 6), rng.randint(1, 3))
                clauses.append([v if rng.getrandbits(1) else -v for v in vs])
            f = CNFFormula.from_raw_clauses(clauses)
            self.assertEqual(solve_incremental(f)["satisfiable"], brute_sat(f))
            self.assertFalse(solve_incremental(f)["promoted"])


if __name__ == "__main__":
    unittest.main()
