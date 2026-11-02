"""Oracle-backed checks of full-CNF flip automorphisms and orbit quotient."""
import unittest
from random import Random

from pysat.solvers import Minisat22
from witnora_core.cnf import CNFFormula
from witnora_core.xor import canonical_xor_cnf_clauses
from scripts.experiment_verified_flip_orbits import (
    benchmark, canonical, discover, enumerate_search, independent_pivots,
    kernel_basis, make_case, satisfies, verified_flip,
)


class VerifiedFlipOrbitTests(unittest.TestCase):
    def test_kernel_and_full_cnf_rejection(self):
        self.assertEqual(set(kernel_basis((0b11,), 2)), {0b11})
        pure = CNFFormula.from_raw_clauses(canonical_xor_cnf_clauses((1, 2), 0))
        self.assertTrue(verified_flip(pure, 0b11))
        self.assertFalse(verified_flip(pure, 0b01))
        broken = CNFFormula.from_raw_clauses(
            (*canonical_xor_cnf_clauses((1, 2), 0), (1,)))
        self.assertFalse(verified_flip(broken, 0b11))

    def test_orbit_canonicalization_and_truth_preservation(self):
        for n in (6, 8):
            for seed in range(8):
                for kind in ("xor_sat", "xor_unsat", "partially_broken", "random_3sat"):
                    f = make_case(n, seed, kind)
                    info = discover(f)
                    generators = tuple(info["pivots"].values())
                    for gen in generators:
                        self.assertTrue(verified_flip(f, gen))
                    span = [0]
                    for gen in generators:
                        span += [x ^ gen for x in span]
                    self.assertEqual(len(set(span)), 1 << info["rank"])
                    for assignment in range(1 << f.max_var):
                        canon = canonical(assignment, info["pivots"])
                        self.assertEqual(canon, min(assignment ^ g for g in span))
                        self.assertEqual(canonical(canon, info["pivots"]), canon)
                        for gen in generators:
                            self.assertEqual(satisfies(f, assignment), satisfies(f, assignment ^ gen))
                            self.assertEqual(canonical(assignment ^ gen, info["pivots"]), canon)

    def test_randomized_oracle_and_visit_count(self):
        for seed in range(90):
            rng = Random(883101 + seed)
            n = rng.randrange(5, 10)
            clauses = []
            for _ in range(rng.randrange(1, 4)):
                support = rng.sample(range(1, n + 1), 3)
                clauses.extend(canonical_xor_cnf_clauses(support, rng.randrange(2)))
            for _ in range(rng.randrange(0, 8)):
                support = rng.sample(range(1, n + 1), 3)
                clauses.append(tuple(v if rng.randrange(2) else -v for v in support))
            f = CNFFormula.from_raw_clauses(clauses)
            info = discover(f)
            plain, _ = enumerate_search(f)
            quot, _ = enumerate_search(f, info["pivots"])
            with Minisat22(bootstrap_with=f.to_clause_lists()) as oracle:
                self.assertEqual(plain, oracle.solve(), seed)
            self.assertEqual(plain, quot, seed)

    def test_smoke(self):
        data = benchmark(seeds=1, repeats=1)
        self.assertEqual(data["summary"]["cases"], 8)
        self.assertTrue(data["summary"]["all_answers_match_minisat"])


if __name__ == "__main__":
    unittest.main()
