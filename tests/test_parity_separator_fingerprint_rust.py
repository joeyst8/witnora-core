"""R-045 source-exact XOR separator observation and adversarial controls."""
from __future__ import annotations

import os
import random
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.xor import canonical_xor_cnf_clauses
from witnora_core.parity_separator_fingerprint import (
    parity_separator_fingerprint, parity_separator_fingerprint_rust,
)


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestNativeParitySeparatorFingerprint(unittest.TestCase):
    def test_1050_random_cnfs_and_all_k_bounds(self):
        rng=random.Random(45112026)
        count=0
        for n in range(2,9):
            for case in range(150):
                source=[
                    [rng.choice((-1,1))*rng.randrange(1,n+1)
                     for _ in range(rng.randrange(7))]
                    for _ in range(rng.randrange(17))
                ]
                formula=CNFFormula.from_raw_clauses(source)
                max_k=rng.randrange(2,7)
                with self.subTest(n=n,case=case,max_k=max_k):
                    native=parity_separator_fingerprint_rust(formula,max_k=max_k)
                    original=parity_separator_fingerprint(formula,max_k=max_k)
                    self.assertEqual(native,original)
                    self.assertFalse(native["cnf_transformed"])
                    self.assertFalse(native["lean_verified"])
                count+=1
        self.assertEqual(count,1050)

    def test_100_planted_hubs_with_non_xor_cross_clause(self):
        rng=random.Random(450063)
        for i in range(100):
            center,a,b=sorted(rng.sample(range(1,60),3))
            clauses=set()
            for u,v,rhs in (
                (center,a,rng.getrandbits(1)),
                (center,b,rng.getrandbits(1)),
            ):
                clauses.update(canonical_xor_cnf_clauses((u,v),rhs))
            # An ordinary 3-clause crossing both spokes is deliberately
            # outside the parity-pattern graph.
            clauses.add(tuple(sorted([center,a,b])))
            formula=CNFFormula.from_raw_clauses(clauses)
            with self.subTest(i=i):
                result=parity_separator_fingerprint_rust(formula)
                self.assertEqual(result,parity_separator_fingerprint(formula))
                self.assertEqual(result["exact_parity_equations"],2)
                self.assertEqual(
                    result["separator_candidates"][0]["variable"],center)
                self.assertFalse(result["non_xor_cross_edges_audited"])

    def test_exact_high_arity_complete_and_incomplete_cases(self):
        variables=tuple(range(1,7))
        for rhs in (0,1):
            expected=canonical_xor_cnf_clauses(variables,rhs)
            complete=CNFFormula.from_raw_clauses(expected)
            missing=CNFFormula.from_raw_clauses(sorted(expected)[1:])
            for max_k in (2,3,4,5,6):
                self.assertEqual(
                    parity_separator_fingerprint_rust(complete,max_k=max_k),
                    parity_separator_fingerprint(complete,max_k=max_k))
                self.assertEqual(
                    parity_separator_fingerprint_rust(missing,max_k=max_k),
                    parity_separator_fingerprint(missing,max_k=max_k))
                n=parity_separator_fingerprint_rust(complete,max_k=max_k)
                self.assertEqual(n["exact_parity_equations"],int(max_k==6))

    def test_invalid_arity_and_empty_source(self):
        formula=CNFFormula.from_raw_clauses([])
        for max_k in (1,7,-10):
            with self.assertRaisesRegex(
                    ValueError,"bounded XOR detection requires arity 2..6"):
                parity_separator_fingerprint_rust(formula,max_k=max_k)
        self.assertEqual(
            parity_separator_fingerprint_rust(formula),
            parity_separator_fingerprint(formula))


if __name__=="__main__":
    unittest.main()
