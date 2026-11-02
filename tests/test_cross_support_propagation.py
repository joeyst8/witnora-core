import unittest
from collections import Counter
from random import Random

from pysat.solvers import Minisat22
from witnora_core.cnf import CNFFormula
from witnora_core.xor import canonical_xor_cnf_clauses
from scripts.experiment_cross_support_propagation import (
    extract_rows, derive_small_rows, make_case, solve,
)


class CrossSupportTests(unittest.TestCase):
    def test_source_bound_cancellation(self):
        f = make_case(16, 0, "imply")
        self.assertIn((0b1100, 0), derive_small_rows(extract_rows(f)))

    def test_all_control_families_against_minisat(self):
        for n in (16, 32):
            for seed in range(8):
                for kind in ("conflict", "imply", "sat", "random"):
                    with self.subTest(n=n, seed=seed, kind=kind):
                        f = make_case(n, seed, kind)
                        with Minisat22(bootstrap_with=f.to_clause_lists()) as oracle:
                            expected = oracle.solve()
                        self.assertEqual(solve(tuple(map(tuple, f.to_clause_lists())),
                                               derive_small_rows(extract_rows(f)), Counter()),
                                         expected)

    def test_random_exact_xor_with_unrelated_clauses(self):
        for seed in range(100):
            rng = Random(seed)
            clauses = []
            for _ in range(3):
                vs = rng.sample(range(1, 9), 3)
                clauses += canonical_xor_cnf_clauses(vs, rng.randrange(2))
            for _ in range(8):
                vs = rng.sample(range(1, 9), 3)
                clauses.append(tuple(v if rng.randrange(2) else -v for v in vs))
            f = CNFFormula.from_raw_clauses(clauses)
            with Minisat22(bootstrap_with=f.to_clause_lists()) as oracle:
                expected = oracle.solve()
            actual = solve(tuple(map(tuple, f.to_clause_lists())),
                           derive_small_rows(extract_rows(f)), Counter())
            self.assertEqual(actual, expected, seed)


if __name__ == "__main__":
    unittest.main()
