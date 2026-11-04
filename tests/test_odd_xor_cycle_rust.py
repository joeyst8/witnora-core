"""R-041 source-bound binary-XOR odd-cycle candidate discovery."""
from __future__ import annotations

import os
import random
import unittest
from itertools import combinations

from witnora_core.cnf import CNFFormula
from witnora_core.cycle_discovery import (
    discover_odd_xor_cycle, discover_odd_xor_cycle_rust,
)
from witnora_core.xor import canonical_xor_cnf_clauses


def verify_candidate(formula, candidate):
    if candidate is None:
        return
    assert candidate["status"] == "UNVERIFIED_STRUCTURAL_CANDIDATE"
    assert candidate["formal_status"] == "NOT_LEAN_VERIFIED"
    clause_set={tuple(clause) for clause in formula.to_clause_lists()}
    position=candidate["start"]
    syndrome=0
    for step in candidate["steps"]:
        nxt,rhs=step["next"],step["rhs"]
        assert canonical_xor_cnf_clauses((position,nxt),rhs).issubset(clause_set)
        syndrome^=rhs
        position=nxt
    assert position==candidate["start"]
    assert syndrome==1


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestNativeOddXorCycle(unittest.TestCase):
    def test_1050_random_sources_exact_candidate_parity(self):
        rng=random.Random(411112026)
        cases=0
        for n in range(2,9):
            pairs=list(combinations(range(1,n+1),2))
            for _ in range(150):
                source=set()
                for u,v in rng.sample(pairs,rng.randrange(min(12,len(pairs))+1)):
                    source.update(canonical_xor_cnf_clauses(
                        (u,v),rng.getrandbits(1)))
                # Incomplete patterns and ordinary 3-CNF should not
                # automatically count as exact binary-XOR equations.
                for _ in range(rng.randrange(4)):
                    source.add(tuple(sorted(
                        rng.choice((-1,1))*rng.randrange(1,n+1)
                        for _ in range(rng.randrange(1,4)))))
                formula=CNFFormula.from_raw_clauses(source)
                ref=discover_odd_xor_cycle(formula)
                native=discover_odd_xor_cycle_rust(formula)
                with self.subTest(n=n):
                    self.assertEqual(native,ref)
                    verify_candidate(formula,native)
                cases+=1
        self.assertEqual(cases,1050)

    def test_100_planted_odd_triangles_and_source_provenance(self):
        rng=random.Random(410024)
        for case in range(100):
            chosen=sorted(rng.sample(range(1,20),3))
            a,b,c=chosen
            x=rng.getrandbits(1)
            y=rng.getrandbits(1)
            source=set()
            for u,v,rhs in ((a,b,x),(b,c,y),(a,c,x^y^1)):
                source.update(canonical_xor_cnf_clauses((u,v),rhs))
            formula=CNFFormula.from_raw_clauses(source)
            with self.subTest(case=case):
                result=discover_odd_xor_cycle_rust(formula)
                self.assertIsNotNone(result)
                self.assertEqual(result,discover_odd_xor_cycle(formula))
                verify_candidate(formula,result)

    def test_single_clause_not_a_complete_xor_pattern(self):
        formula=CNFFormula.from_raw_clauses([[1,2],[3,4]])
        self.assertIsNone(discover_odd_xor_cycle_rust(formula))


if __name__=="__main__":
    unittest.main()
