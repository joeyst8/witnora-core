"""R-048 all three graph-invariant DP policies, exact CNF parity and SAT."""
from __future__ import annotations

import os
import random
import unittest
from itertools import product

from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.structural_operator_invention import (
    graph_invariants, graph_invariants_rust,
    eliminate_with_policy, eliminate_with_policy_rust,
    min_fill_elimination, min_fill_elimination_rust,
    xor_boundary_elimination, xor_boundary_elimination_rust,
    max_release_elimination, max_release_elimination_rust,
)


def brute_sat(formula):
    return any(formula_satisfied(formula, dict(zip(formula.variables,values)))
               for values in product((False,True),repeat=formula.num_vars))


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestNativeInvariantPolicies(unittest.TestCase):
    def test_1200_random_sources_all_three_policy_decisions(self):
        rng=random.Random(48112026)
        count=0
        for n in range(1,9):
            for case in range(150):
                source=[
                    [rng.choice((-1,1))*rng.randrange(1,n+1)
                     for _ in range(rng.randrange(6))]
                    for _ in range(rng.randrange(14))
                ]
                formula=CNFFormula.from_raw_clauses(source)
                pair=rng.choice((0,1,2,4,12,20))
                growth=rng.choice((-2,0,1,2,4))
                with self.subTest(n=n,case=case):
                    self.assertEqual(
                        graph_invariants_rust(formula),
                        graph_invariants(formula))
                    for policy in ("min_fill","xor_boundary","max_release"):
                        py=eliminate_with_policy(
                            formula,policy,max_pairs=pair,
                            max_clause_growth=growth)
                        rs=eliminate_with_policy_rust(
                            formula,policy,max_pairs=pair,
                            max_clause_growth=growth)
                        self.assertEqual(rs,py)
                        self.assertEqual(brute_sat(rs),brute_sat(formula))
                count+=1
        self.assertEqual(count,1200)

    def test_named_adapters_and_invalid_policy(self):
        formula=CNFFormula.from_raw_clauses([
            [1,2],[-1,2],[2,-3],[3,-4],[-3,4],
        ])
        for native,original in (
            (min_fill_elimination_rust,min_fill_elimination),
            (xor_boundary_elimination_rust,xor_boundary_elimination),
            (max_release_elimination_rust,max_release_elimination),
        ):
            self.assertEqual(native(formula),original(formula))
        for impl in (eliminate_with_policy,eliminate_with_policy_rust):
            with self.assertRaisesRegex(
                    ValueError,"unknown invariant-guided elimination policy"):
                impl(formula,"NO_SUCH_POLICY")
        self.assertEqual(
            eliminate_with_policy_rust(formula,"min_fill",max_pairs=-1),
            formula)


if __name__=="__main__":
    unittest.main()
