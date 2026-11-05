"""Independent W021 n=16 source, DPLL, truth and modular-rank controls."""

from __future__ import annotations

import json
import os
import subprocess
import unittest

from tests.test_signed_covariance_rust import covariance_matrix,next_random
from tests.test_hybrid_refutation_rust import verify_xor

BIN=os.environ.get("WITNORA_RUST_COST_AWARE_BIN")
N=16
MASK=(1<<32)-1
P=65521
SEEDS={
    "planted_sat_16_68":0xD21C0DE1,
    "uniform_boundary_16_68":0xD21C0DE2,
    "eight_core_unsat_16_68":0xD21C0DE3,
    "padded_2sat_unsat_16_68":0xD21C0DE4,
    "xor_cycle_unsat_16_68":0xD21C0DE5,
}
PARITY=[((1,2,3),0),((1,4,5),0),((2,4,6),0),((3,5,6),1)]


def source(name:str,index:int)->list[list[int]]:
    state=SEEDS[name]^(((index+1)*0x9E3779B9)&MASK)
    clauses=[]
    if name=="eight_core_unsat_16_68":
        clauses.extend([[-v if bits&(1<<(v-1)) else v for v in (1,2,3)]
                        for bits in range(8)])
    if name=="padded_2sat_unsat_16_68":
        for a in (0,1):
            for b in (0,1):
                x=-1 if a else 1
                y=-2 if b else 2
                z=3+a*2+b
                clauses.extend([[x,y,z],[x,y,-z]])
    if name=="xor_cycle_unsat_16_68":
        for vars,rhs in PARITY:
            for bits in range(8):
                if bits.bit_count()%2==rhs:continue
                clauses.append([-v if bits&(1<<j) else v
                                for j,v in enumerate(vars)])
    while len(clauses)<68:
        seen=set()
        clause=[]
        while len(clause)<3:
            state=next_random(state)
            v=state%N+1
            if v in seen:continue
            seen.add(v)
            state=next_random(state)
            clause.append(-v if state&1 else v)
        if name=="planted_sat_16_68" and all(lit>0 for lit in clause):continue
        clauses.append(clause)
    permutation=list(range(1,N+1))
    for i in range(N-1,0,-1):
        state=next_random(state)
        j=state%(i+1)
        permutation[i],permutation[j]=permutation[j],permutation[i]
    flips=[]
    for _ in range(N):
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


def moments(clauses:list[list[int]])->int:
    # Assignment's restriction to a clause must match its unique
    # falsifying bit-pattern; no SAT-solver assumptions needed.
    patterns=[]
    for clause in clauses:
        scope=sum(1<<(abs(lit)-1) for lit in clause)
        needed=sum(1<<(abs(lit)-1) for lit in clause if lit<0)
        patterns.append((scope,needed))
    return sum(not any(a&scope==needed for scope,needed in patterns)
               for a in range(1<<N))


def violated(clause:list[int],assignment:int)->bool:
    return not any(bool(assignment&(1<<(abs(lit)-1)))==(lit>0)
                   for lit in clause)


def independent_dpll(clauses:list[list[int]])->dict[str,int|bool]:
    degree=[sum(abs(lit)==v+1 for clause in clauses for lit in clause)
            for v in range(N)]
    order=sorted(range(N),key=lambda v:(-degree[v],v))
    nodes=scans=0

    def visit(original:tuple[bool|None,...])->bool:
        nonlocal nodes,scans
        nodes+=1
        values=list(original)
        while True:
            changed=False
            for clause in clauses:
                scans+=1
                if any(values[abs(lit)-1] is not None
                       and values[abs(lit)-1]==(lit>0) for lit in clause):continue
                free=[lit for lit in clause if values[abs(lit)-1] is None]
                if not free:return False
                if len(free)==1:
                    lit=free[0]
                    values[abs(lit)-1]=lit>0
                    changed=True
            if not changed:break
        for clause in clauses:
            scans+=1
            if not any(values[abs(lit)-1] is not None
                       and values[abs(lit)-1]==(lit>0) for lit in clause):
                break
        else:return True
        branch=next(v for v in order if values[v] is None)
        for choice in (False,True):
            alt=values.copy()
            alt[branch]=choice
            if visit(tuple(alt)):return True
        return False

    sat=visit((None,)*N)
    return {"sat":sat,"nodes":nodes,"scans":scans}


def modular_rank(matrix:list[list[int]],append:bool)->int:
    m=len(matrix)
    basis={}
    for raw in matrix+([[1]*m] if append else []):
        row=[v%P for v in raw]
        while True:
            pivot=next((i for i,v in enumerate(row) if v),None)
            if pivot is None:break
            if pivot not in basis:
                inv=pow(row[pivot],P-2,P)
                basis[pivot]=[x*inv%P for x in row]
                break
            coeff=row[pivot]
            reference=basis[pivot]
            row=[(a-coeff*b)%P for a,b in zip(row,reference)]
    return len(basis)


@unittest.skipUnless(BIN,"compiled W021 release Rust binary unavailable")
class CostAwareGeometryIndependentOracle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(subprocess.run([BIN],check=True,capture_output=True,
                                             text=True,timeout=300).stdout)

    def test_predeclared_families_and_cost_accounting(self):
        self.assertEqual(self.report["research_id"],"W-CROSSDOMAIN-021")
        self.assertEqual(self.report["prime"],P)
        self.assertEqual(self.report["timing_repetitions"],3)
        self.assertEqual({x["family"] for x in self.report["families"]},set(SEEDS))
        for family in self.report["families"]:
            self.assertEqual(family["cases"],12)
            self.assertEqual(family["satisfiable"]+family["unsatisfiable"],12)
            self.assertEqual(sum(family[k] for k in (
                "covariance_proofs","xor_proofs","dpll_fallbacks")),12)
            self.assertEqual([x["index"] for x in family["controls"]],[0,1,11])
            for key in ("mean_case_median_dpll_ns",
                        "mean_case_median_exact_first_ns",
                        "mean_case_median_modular_screen_ns"):
                self.assertGreater(family[key],0)
            if family["family"]=="planted_sat_16_68":
                self.assertEqual(family["satisfiable"],12)
            if family["family"] in ("eight_core_unsat_16_68",
                                      "padded_2sat_unsat_16_68",
                                      "xor_cycle_unsat_16_68"):
                self.assertEqual(family["unsatisfiable"],12)

    def test_independent_truth_dpll_covariance_xor_and_field_rank(self):
        for family in self.report["families"]:
            for control in family["controls"]:
                with self.subTest(family=family["family"],index=control["index"]):
                    clauses=source(family["family"],control["index"])
                    self.assertEqual(clauses,control["source"])
                    independent=independent_dpll(clauses)
                    self.assertEqual(independent["scans"],control["dpll_scans"])
                    self.assertEqual(independent["sat"],control["sat"])
                    self.assertEqual(moments(clauses)>0,control["sat"])
                    k=covariance_matrix(clauses)
                    self.assertEqual(modular_rank(k,True)>modular_rank(k,False),
                                     control["modular_candidate"])
                    if control["covariance_weights"] is not None:
                        w=[int(v) for v in control["covariance_weights"]]
                        self.assertEqual(len(w),len(clauses))
                        self.assertNotEqual(sum(w),0)
                        self.assertTrue(all(sum(a*b for a,b in zip(row,w))==0 for row in k))
                        self.assertEqual(sum(w)%8,0)
                        weighted=[(clause,weight) for clause,weight in zip(clauses,w)
                                  if weight]
                        for assignment in range(1<<N):
                            energy=sum(weight for clause,weight in weighted
                                       if violated(clause,assignment))
                            self.assertEqual(energy,sum(w)//8)
                        self.assertFalse(control["sat"])
                    if control["xor_equations"] is not None:
                        verify_xor(clauses,control["xor_equations"])
                        self.assertFalse(control["sat"])


if __name__=="__main__":
    unittest.main()
