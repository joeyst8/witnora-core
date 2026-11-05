"""Independent W025 audit via explicit spin Hamiltonian and exact enumeration."""
import collections
import json
import math
import os
import subprocess
import unittest

TRIPLES=((1,2,3),(1,4,5),(2,4,6),(3,5,6),(7,8,9))
SAT=(0,0,0,0,1)
UNSAT=(0,0,0,1,0)
BETAS=(0.0,0.25,0.5,1.0,2.0,4.0)

def xorshift(s):
    s ^= (s << 13) & 0xFFFFFFFF
    s ^= s >> 17
    s ^= (s << 5) & 0xFFFFFFFF
    return s & 0xFFFFFFFF

def reconstruct(index):
    seed=0xD24F0240 ^ (((index+1)*0x9E3779B9) & 0xFFFFFFFF)
    state=seed
    names=list(range(1,10))
    for k in range(8,0,-1):
        state=xorshift(state)
        j=state%(k+1)
        names[k],names[j]=names[j],names[k]
    return seed,[tuple(names[v-1] for v in edge) for edge in TRIPLES]

def gauge_mask(i,j):
    return (((i+1)*0x9E3779B9) ^ ((j+1)*0x85EBCA6B) ^ 0x02502425) & 0x1FF

def gauge(rhs,edges,flips):
    return tuple(parity ^ (sum((flips>>(v-1))&1 for v in edge)%2)
                 for edge,parity in zip(edges,rhs))

def cycles(edges):
    masks=[sum(1<<(v-1) for v in edge) for edge in edges]
    out=[]
    for subset in range(1,32):
        x=0
        for i,mask in enumerate(masks):
            if (subset>>i)&1:
                x ^= mask
        if x==0:
            out.append(subset)
    return out

def holonomy(rhs,subset):
    parity=0
    for j,b in enumerate(rhs):
        if (subset>>j)&1:
            parity ^= b
    return -1 if parity else 1

def spin_hist(edges,rhs):
    counts=collections.Counter()
    for assignment in range(512):
        spins=[-1 if (assignment>>i)&1 else 1 for i in range(9)]
        energy=0
        for edge,parity in zip(edges,rhs):
            coupling=-1 if parity else 1
            product=math.prod(spins[v-1] for v in edge)
            energy -= coupling*product
        counts[energy]+=1
    return dict(sorted(counts.items()))

def partition(hist,beta):
    return sum(count*math.exp(-beta*energy) for energy,count in hist.items())

def formula(h,beta):
    return 512*math.cosh(beta)**5*(1+h*math.tanh(beta)**4)

class W025IndependentTest(unittest.TestCase):
    def test_all_source_and_gauge_controls(self):
        executable=os.environ.get("WITNORA_RUST_SPIN_BIN")
        self.assertTrue(executable and os.path.isfile(executable),"set WITNORA_RUST_SPIN_BIN")
        result=subprocess.run([executable,"--json"],check=True,capture_output=True,text=True)
        report=json.loads(result.stdout)
        self.assertEqual(report["study"],"W-CROSSDOMAIN-025")
        self.assertEqual(report["case_count"],64)
        self.assertEqual(report["gauge_interventions_per_case"],16)
        self.assertEqual(report["inverse_temperatures_beta"],list(BETAS))
        self.assertEqual(len(report["cases"]),64)
        for i,case in enumerate(report["cases"]):
            with self.subTest(index=i):
                seed,edges=reconstruct(i)
                self.assertEqual(case["seed"],seed)
                self.assertEqual(case["source_triples"],[list(e) for e in edges])
                self.assertEqual(cycles(edges),[15])
                self.assertEqual(case["cycle_source_indices_zero_based"],[0,1,2,3])
                self.assertEqual((case["sat_holonomy"],case["unsat_holonomy"]),(1,-1))
                self.assertEqual(len(case["gauge_masks"]),16)
                for rhs,h,label in ((SAT,1,"sat"),(UNSAT,-1,"unsat")):
                    base=spin_hist(edges,rhs)
                    self.assertEqual(holonomy(rhs,15),h)
                    self.assertEqual({str(k):v for k,v in base.items()},case[label+"_energy_histogram"])
                    self.assertEqual((min(base),base[min(base)]),
                                     (-5,32) if label=="sat" else (-3,128))
                    for j,beta in enumerate(BETAS):
                        z=partition(base,beta)
                        self.assertTrue(math.isclose(z,formula(h,beta),rel_tol=1e-10))
                        self.assertTrue(math.isclose(z,case[label+"_partitions"][j],rel_tol=1e-10))
                    for j in range(16):
                        flips=gauge_mask(i,j)
                        self.assertEqual(case["gauge_masks"][j],flips)
                        rhs_new=gauge(rhs,edges,flips)
                        self.assertEqual(holonomy(rhs_new,15),h)
                        self.assertEqual(spin_hist(edges,rhs_new),base)
                self.assertTrue(case["all_gauges_exactly_energy_invariant"])
                self.assertTrue(case["all_partitions_match_analytic"])

if __name__=="__main__":
    unittest.main()
