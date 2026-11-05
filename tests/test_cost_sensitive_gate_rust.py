"""R-049 cost-sensitive fixed-threshold training and application parity."""
from __future__ import annotations

import os
import random
import unittest
from itertools import product
from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.cost_sensitive_gate import (
    choose_threshold, choose_threshold_rust,
    cost_sensitive_pivot, cost_sensitive_pivot_rust, THRESHOLDS,
)


def brute_sat(formula):
    return any(formula_satisfied(formula,dict(zip(formula.variables,bits)))
               for bits in product((False,True),repeat=formula.num_vars))


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestNativeCostGate(unittest.TestCase):
    def test_500_training_sets_exact_decisions(self):
        rng=random.Random(49112026)
        for case in range(500):
            observations=[]
            for _ in range(rng.randrange(1,32)):
                observations.append({
                    "mixed_pivots":rng.randrange(0,15),
                    "variables":rng.randrange(1,40),
                    "clauses":rng.randrange(1,190),
                    "adaptive_score":rng.uniform(-10,20),
                    "greedy_score":rng.uniform(-10,20),
                    "adaptive_ms":rng.uniform(0,5),
                    "greedy_ms":rng.uniform(0,5),
                })
            weight=rng.choice((0.0,0.25,1.0,2.0,10.0))
            with self.subTest(case=case):
                self.assertEqual(
                    choose_threshold_rust(observations,cost_weight=weight),
                    choose_threshold(observations,cost_weight=weight))

    def test_960_frozen_inference_sources(self):
        rng=random.Random(49212026)
        modes=set()
        count=0
        for n in range(1,9):
            for case in range(120):
                formula=CNFFormula.from_raw_clauses([
                    [rng.choice((-1,1))*rng.randrange(1,n+1)
                     for _ in range(rng.randrange(5))]
                    for _ in range(rng.randrange(15))
                ])
                threshold=rng.choice(THRESHOLDS)
                budget=rng.choice((0,1,3,8,12))
                with self.subTest(n=n,case=case):
                    py=cost_sensitive_pivot(
                        formula,threshold=threshold,max_pairs=budget)
                    rs=cost_sensitive_pivot_rust(
                        formula,threshold=threshold,max_pairs=budget)
                    self.assertEqual(rs,py)
                    self.assertEqual(brute_sat(rs[0]),brute_sat(formula))
                    modes.add(rs[1]["mode"])
                count+=1
        self.assertEqual(count,960)
        self.assertEqual(modes,{"adaptive","greedy"})

    def test_invalid_threshold_and_training_penalty(self):
        formula=CNFFormula.from_raw_clauses([[1,2],[-1,2]])
        for impl in (cost_sensitive_pivot,cost_sensitive_pivot_rust):
            for params in ({"threshold":1},{"threshold":2,"max_pairs":-1}):
                with self.assertRaisesRegex(
                        ValueError,"threshold must come from the preregistered set"):
                    impl(formula,**params)
        for impl in (choose_threshold,choose_threshold_rust):
            for observations,weight in (([],2.0),([{
                "mixed_pivots":2,"variables":2,"clauses":2,
                "adaptive_score":1.0,"greedy_score":1.0,
                "adaptive_ms":1.0,"greedy_ms":1.0,
            }],-1.0)):
                with self.assertRaisesRegex(
                        ValueError,"missing observations or invalid penalty"):
                    impl(observations,cost_weight=weight)


if __name__=="__main__":
    unittest.main()
