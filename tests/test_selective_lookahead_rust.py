"""R-044 native selective pivot: full routing and exact Python parity."""
from __future__ import annotations

import os
import random
import unittest
from itertools import product

from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.selective_lookahead_prototype import (
    cheap_pivot_features, cheap_pivot_features_rust,
    selective_pivot, selective_pivot_rust,
)


def brute_sat(formula):
    return any(formula_satisfied(formula, dict(zip(formula.variables, values)))
               for values in product((False,True),repeat=formula.num_vars))


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestNativeSelectiveLookahead(unittest.TestCase):
    def test_1120_randomized_routing_and_complete_metadata(self):
        rng=random.Random(44112026)
        modes=set()
        cases=0
        for n in range(1,9):
            for case in range(140):
                rows=[
                    [rng.choice((-1,1))*rng.randrange(1,n+1)
                     for _ in range(rng.randrange(5))]
                    for _ in range(rng.randrange(14))
                ]
                formula=CNFFormula.from_raw_clauses(rows)
                params={
                    "max_pairs":rng.choice((0,1,2,4,12)),
                    "min_mixed_pivots":rng.randrange(1,5),
                    "max_vars":rng.randrange(1,10),
                    "max_clauses":rng.randrange(1,15),
                    "expansion_budget":rng.randrange(1,35),
                }
                with self.subTest(n=n,case=case):
                    expected_features=cheap_pivot_features(
                        formula,max_pairs=params["max_pairs"])
                    actual_features=cheap_pivot_features_rust(
                        formula,max_pairs=params["max_pairs"])
                    self.assertEqual(actual_features,expected_features)
                    expected, expected_meta=selective_pivot(formula,**params)
                    actual, actual_meta=selective_pivot_rust(formula,**params)
                    self.assertEqual(actual,expected)
                    self.assertEqual(actual_meta,expected_meta)
                    self.assertEqual(brute_sat(actual),brute_sat(formula))
                    modes.add(actual_meta["mode"])
                cases+=1
        self.assertEqual(cases,1120)
        self.assertEqual(modes,{"greedy","adaptive"})

    def test_eligibility_late_budget_validation_and_invalid_params(self):
        formula=CNFFormula.from_raw_clauses([
            [1,2],[-1,3],[1,-3],[-1,-2],
        ])
        for min_mixed,mode in ((1,"adaptive"),(4,"greedy")):
            original, metadata=selective_pivot(
                formula,min_mixed_pivots=min_mixed)
            native, native_meta=selective_pivot_rust(
                formula,min_mixed_pivots=min_mixed)
            self.assertEqual((native,native_meta),(original,metadata))
            self.assertEqual(native_meta["mode"],mode)
        with self.assertRaisesRegex(
                ValueError,"invalid adaptive lookahead budget"):
            selective_pivot_rust(formula,min_mixed_pivots=1,
                                 expansion_budget=1001)
        self.assertEqual(
            selective_pivot_rust(formula,min_mixed_pivots=4,
                                 expansion_budget=1001),
            selective_pivot(formula,min_mixed_pivots=4,
                            expansion_budget=1001))
        for kwargs in (
            {"max_pairs":-1},
            {"min_mixed_pivots":0},
            {"max_vars":0},
            {"max_clauses":0},
            {"expansion_budget":0},
        ):
            for impl in (selective_pivot,selective_pivot_rust):
                with self.assertRaisesRegex(
                        ValueError,"invalid selective lookahead gate"):
                    impl(formula,**kwargs)


if __name__=="__main__":
    unittest.main()
