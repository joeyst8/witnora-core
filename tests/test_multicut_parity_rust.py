"""R-047 full bounded parity 1..3 cut parity and cut-budget controls."""
from __future__ import annotations

import os
import random
import unittest
from witnora_core.cnf import CNFFormula
from witnora_core.xor import canonical_xor_cnf_clauses
from witnora_core.multicut_parity_separator import (
    bounded_parity_separators, bounded_parity_separators_rust,
)


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestNativeMulticutParity(unittest.TestCase):
    def test_960_seeded_sources_complete_metadata(self):
        rng=random.Random(47112026)
        count=0
        for n in range(2,10):
            for case in range(120):
                clauses=set()
                for _ in range(rng.randrange(0,8)):
                    chosen=rng.sample(range(1,n+1),
                                      rng.randrange(2,min(n,6)+1))
                    clauses.update(canonical_xor_cnf_clauses(
                        chosen,rng.getrandbits(1)))
                for _ in range(rng.randrange(5)):
                    clauses.add(tuple(
                        rng.choice((-1,1))*rng.randrange(1,n+1)
                        for _ in range(rng.randrange(5))))
                formula=CNFFormula.from_raw_clauses(clauses)
                budgets={
                    "max_cut":rng.randrange(1,4),
                    "max_shared":rng.randrange(1,11),
                    "max_trials":rng.randrange(1,35),
                }
                with self.subTest(n=n,case=case):
                    native=bounded_parity_separators_rust(formula,**budgets)
                    python=bounded_parity_separators(formula,**budgets)
                    self.assertEqual(native,python)
                    self.assertFalse(native["full_cnf_separation_verified"])
                    self.assertFalse(native["lean_verified"])
                count+=1
        self.assertEqual(count,960)

    def test_120_planted_minimal_1_2_3_variable_cuts(self):
        rng=random.Random(470063)
        for size in (1,2,3):
            for case in range(40):
                shared=rng.sample(range(1,40),size)
                left,right=rng.sample(range(41,80),2)
                clauses=set()
                for terminal in (left,right):
                    clauses.update(canonical_xor_cnf_clauses(
                        (*shared,terminal),rng.getrandbits(1)))
                formula=CNFFormula.from_raw_clauses(clauses)
                with self.subTest(size=size,case=case):
                    py=bounded_parity_separators(
                        formula,max_cut=3,max_shared=18,max_trials=2000)
                    rs=bounded_parity_separators_rust(
                        formula,max_cut=3,max_shared=18,max_trials=2000)
                    self.assertEqual(rs,py)
                    self.assertTrue(rs["candidate_cuts"])
                    self.assertEqual(rs["smallest_cut_size"],size)
                    self.assertIn(sorted(shared),
                                  [c["variables"] for c in rs["candidate_cuts"]])

    def test_exhaustion_and_budget_validations(self):
        formula=CNFFormula.from_raw_clauses([
            [1,-2],[-1,2],[1,-3],[-1,3],
        ])
        for trials in (1,2,3,4):
            self.assertEqual(
                bounded_parity_separators_rust(formula,max_trials=trials),
                bounded_parity_separators(formula,max_trials=trials))
        for params in (
            {"max_cut":0},{"max_cut":4},
            {"max_shared":0},{"max_trials":0},
        ):
            for impl in (bounded_parity_separators,
                         bounded_parity_separators_rust):
                with self.assertRaisesRegex(
                        ValueError,"invalid bounded separator search"):
                    impl(formula,**params)


if __name__=="__main__":
    unittest.main()
