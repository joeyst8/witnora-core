"""R-046 complete native spoke-equation, path and contradiction parity."""
from __future__ import annotations

import os
import random
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.xor import canonical_xor_cnf_clauses
from witnora_core.spoke_discovery import (
    extract_binary_xor_equations, extract_binary_xor_equations_rust,
    extract_spoke_paths, extract_spoke_paths_rust,
    discover_parity_spoke_conflicts, discover_parity_spoke_conflicts_rust,
)


def verify_source_witnesses(formula, conflicts):
    source={tuple(c) for c in formula.to_clause_lists()}
    for conflict in conflicts:
        assert conflict["status"]=="UNVERIFIED_STRUCTURAL_CANDIDATE"
        assert conflict["formal_status"]=="NOT_LEAN_VERIFIED"
        assert len(conflict["paths"])==2
        p,q=conflict["paths"]
        assert p["middle"]!=q["middle"]
        assert p["syndrome"]!=q["syndrome"]
        for path in conflict["paths"]:
            assert len(path["equations"])==2
            syndrome=0
            for eq in path["equations"]:
                expected=canonical_xor_cnf_clauses(
                    eq["variables"],eq["rhs"])
                assert set(tuple(row) for row in eq["source_clauses"])==expected
                assert expected.issubset(source)
                syndrome^=eq["rhs"]
            assert path["syndrome"]==syndrome


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestNativeSpokeDiscovery(unittest.TestCase):
    def test_1200_random_sources_all_three_outputs(self):
        rng=random.Random(46112026)
        count=0
        for n in range(2,10):
            for case in range(150):
                source=set()
                vars_=list(range(1,n+1))
                for _ in range(rng.randrange(0,min(14,n*n)+1)):
                    u,v=rng.sample(vars_,2)
                    source.update(canonical_xor_cnf_clauses(
                        (u,v),rng.getrandbits(1)))
                for _ in range(rng.randrange(5)):
                    source.add(tuple(rng.choice((-1,1))*
                                     rng.randrange(1,n+1)
                                     for _ in range(rng.randrange(1,5))))
                formula=CNFFormula.from_raw_clauses(source)
                with self.subTest(n=n,case=case):
                    self.assertEqual(
                        extract_binary_xor_equations_rust(formula),
                        extract_binary_xor_equations(formula))
                    self.assertEqual(
                        extract_spoke_paths_rust(formula),
                        extract_spoke_paths(formula))
                    native=discover_parity_spoke_conflicts_rust(formula)
                    self.assertEqual(native,discover_parity_spoke_conflicts(formula))
                    verify_source_witnesses(formula,native)
                count+=1
        self.assertEqual(count,1200)

    def test_100_planted_incompatible_two_spoke_routes(self):
        rng=random.Random(460063)
        for i in range(100):
            a,b,m1,m2=sorted(rng.sample(range(1,60),4))
            clauses=set()
            for u,v,rhs in ((a,m1,0),(b,m1,0),(a,m2,0),(b,m2,1)):
                clauses.update(canonical_xor_cnf_clauses((u,v),rhs))
            formula=CNFFormula.from_raw_clauses(clauses)
            native=discover_parity_spoke_conflicts_rust(formula)
            with self.subTest(i=i):
                self.assertEqual(native,discover_parity_spoke_conflicts(formula))
                self.assertTrue(native)
                verify_source_witnesses(formula,native)

    def test_incomplete_patterns_do_not_create_candidates(self):
        formula=CNFFormula.from_raw_clauses([[1,2],[2,3],[-3,4]])
        self.assertEqual(extract_binary_xor_equations_rust(formula),[])
        self.assertEqual(extract_spoke_paths_rust(formula),[])
        self.assertEqual(discover_parity_spoke_conflicts_rust(formula),[])


if __name__=="__main__":
    unittest.main()
