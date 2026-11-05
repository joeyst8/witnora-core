"""Independent W020 source, exact covariance, XOR and resolution controls."""

from __future__ import annotations

import json
import os
import subprocess
import unittest

from tests.test_signed_covariance_rust import covariance_matrix,next_random
from tests.test_hybrid_refutation_rust import verify_xor
from tests.test_zero_variance_refutation_rust import models,violated

BIN=os.environ.get("WITNORA_RUST_SEPARATION_BIN")
MASK=(1<<32)-1
SEEDS={
    "fresh_planted_sat_48":0xD20C0DE1,
    "fresh_uniform_boundary_48":0xD20C0DE2,
    "disguised_2sat_unsat_56":0xD20C0DE3,
    "full_eight_unsat_56":0xD20C0DE4,
    "parity_cycle_unsat_64":0xD20C0DE5,
}
PARITY=[((1,2,3),0),((1,4,5),0),((2,4,6),0),((3,5,6),1)]


def source(name: str,index: int)->list[list[int]]:
    state=SEEDS[name]^(((index+1)*0x9E3779B9)&MASK)
    clauses=[]
    if name=="disguised_2sat_unsat_56":
        for a in (0,1):
            for b in (0,1):
                x=-1 if a else 1
                y=-2 if b else 2
                v=3+a*2+b
                clauses.extend([[x,y,v],[x,y,-v]])
    if name=="full_eight_unsat_56":
        for bits in range(8):
            clauses.append([-v if bits&(1<<(v-1)) else v for v in (1,2,3)])
    if name=="parity_cycle_unsat_64":
        for triple,rhs in PARITY:
            for bits in range(8):
                if bits.bit_count()%2==rhs:
                    continue
                clauses.append([-v if bits&(1<<j) else v
                                for j,v in enumerate(triple)])
    count=64 if name=="parity_cycle_unsat_64" else (
        56 if name in ("disguised_2sat_unsat_56","full_eight_unsat_56") else 48)
    while len(clauses)<count:
        seen=set()
        clause=[]
        while len(clause)<3:
            state=next_random(state)
            v=1+state%12
            if v in seen:
                continue
            seen.add(v)
            state=next_random(state)
            clause.append(-v if state&1 else v)
        if name=="fresh_planted_sat_48" and all(lit>0 for lit in clause):
            continue
        clauses.append(clause)
    permutation=list(range(1,13))
    for i in range(11,0,-1):
        state=next_random(state)
        j=state%(i+1)
        permutation[i],permutation[j]=permutation[j],permutation[i]
    flips=[]
    for _ in range(12):
        state=next_random(state)
        flips.append(state&1)
    clauses=[[
        (-1 if bool(lit<0)^bool(flips[abs(lit)-1]) else 1)
        *permutation[abs(lit)-1] for lit in clause]
        for clause in clauses]
    for i in range(len(clauses)-1,0,-1):
        state=next_random(state)
        j=state%(i+1)
        clauses[i],clauses[j]=clauses[j],clauses[i]
    return clauses


def independent_binary_resolvents(clauses: list[list[int]])->set[tuple[int,int]]:
    # Compare every unordered source pair, independently of Rust's
    # grouped-pivot implementation.
    derived=set()
    for i,a in enumerate(clauses):
        for b in clauses[i+1:]:
            shared=set(a)&set(b)
            if len(shared)!=2:
                continue
            only_a=set(a)-shared
            only_b=set(b)-shared
            if len(only_a)==len(only_b)==1 and next(iter(only_a))==-next(iter(only_b)):
                derived.add(tuple(sorted(shared)))
    return derived


def independent_binary_unsat(binary: set[tuple[int,int]])->bool:
    # Brute-force independent oracle for Rust's implication closure.
    return not any(all(any(bool(a&(1<<(abs(lit)-1)))==(lit>0)
                           for lit in clause) for clause in binary)
                   for a in range(1<<12))


@unittest.skipUnless(BIN,"compiled W020 Rust executable unavailable")
class SeparationBaselinesIndependentOracle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(subprocess.run([BIN],check=True,capture_output=True,
                                             text=True,timeout=300).stdout)

    def test_frozen_cohorts_and_separation(self):
        self.assertEqual(self.report["research_id"],"W-CROSSDOMAIN-020")
        self.assertEqual({f["family"] for f in self.report["families"]},set(SEEDS))
        for family in self.report["families"]:
            with self.subTest(family=family["family"]):
                self.assertEqual(family["formulas"],32)
                self.assertEqual(family["satisfiable"]+family["unsatisfiable"],32)
                for name in ("covariance_proofs","xor_proofs","resolution_proofs",
                             "covariance_without_xor",
                             "covariance_unique_against_xor_and_resolution",
                             "xor_unique_against_covariance_and_resolution"):
                    self.assertLessEqual(family[name],family["unsatisfiable"])
                if family["family"]=="fresh_planted_sat_48":
                    self.assertEqual(family["satisfiable"],32)
                    self.assertEqual((family["covariance_proofs"],family["xor_proofs"],
                                      family["resolution_proofs"]),(0,0,0))
                if family["family"]=="disguised_2sat_unsat_56":
                    self.assertEqual((family["covariance_proofs"],family["xor_proofs"],
                                      family["resolution_proofs"]),(32,0,32))
                if family["family"]=="full_eight_unsat_56":
                    self.assertEqual((family["covariance_proofs"],family["xor_proofs"],
                                      family["resolution_proofs"]),(32,32,32))
                if family["family"]=="parity_cycle_unsat_64":
                    self.assertEqual((family["unsatisfiable"],family["xor_proofs"]),(32,32))
                self.assertEqual([c["index"] for c in family["controls"]],[0,1,31])

    def test_source_full_truth_and_exact_replay(self):
        for family in self.report["families"]:
            all_sat=0
            for index in range(32):
                all_sat+=models(source(family["family"],index))>0
            self.assertEqual(all_sat,family["satisfiable"])
            for control in family["controls"]:
                with self.subTest(family=family["family"],index=control["index"]):
                    clauses=source(family["family"],control["index"])
                    self.assertEqual(clauses,control["source"])
                    self.assertEqual(models(clauses),control["models"])
                    weights=control["covariance_weights"]
                    if weights is not None:
                        weights=[int(w) for w in weights]
                        self.assertEqual(len(weights),len(clauses))
                        self.assertNotEqual(sum(weights),0)
                        k=covariance_matrix(clauses)
                        self.assertTrue(all(sum(a*b for a,b in zip(row,weights))==0
                                            for row in k))
                        for assignment in range(1<<12):
                            self.assertEqual(sum(w for c,w in zip(clauses,weights)
                                                 if violated(c,assignment))*8,sum(weights))
                    if control["xor_equations"] is not None:
                        verify_xor(clauses,control["xor_equations"])
                    observed=set()
                    for r in control["binary_resolvents"]:
                        pair=tuple(r["binary_clause"])
                        ids=r["source_indices"]
                        self.assertEqual(len(ids),2)
                        a,b=[clauses[i] for i in ids]
                        self.assertTrue(set(pair).issubset(a) and set(pair).issubset(b))
                        self.assertEqual((set(a)-set(pair)).pop(),
                                         -(set(b)-set(pair)).pop())
                        observed.add(pair)
                    self.assertEqual(observed,independent_binary_resolvents(clauses))
                    self.assertEqual(control["resolution_unsat"],
                                     independent_binary_unsat(observed))
                    if weights is not None or control["xor_equations"] is not None \
                        or control["resolution_unsat"]:
                        self.assertEqual(control["models"],0)


if __name__=="__main__":
    unittest.main()
