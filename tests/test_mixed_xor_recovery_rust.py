"""Independent source-side audit of W026 Rust mixed-CNF XOR extraction."""
import collections
import json
import os
import subprocess
import unittest

TRIPLES=((1,2,3),(1,4,5),(2,4,6),(3,5,6),(7,8,9))
SAT=(0,0,0,0,1)
UNSAT=(0,0,0,1,0)
SIZES=(0,32,256,1024,4096,8192)
MASK32=0xFFFFFFFF
MASK64=0xFFFFFFFFFFFFFFFF

def rng(s):
    s ^= (s<<13)&MASK32
    s ^= s>>17
    s ^= (s<<5)&MASK32
    return s&MASK32

def core(rhs):
    out=[]
    for edge,parity in zip(TRIPLES,rhs):
        for pattern in range(8):
            if pattern.bit_count()%2!=parity:
                out.append([(-v if (pattern>>j)&1 else v) for j,v in enumerate(edge)])
    return out

def planted(literal):
    return (abs(literal)==7)==(literal>0)

def make_noise(d,r):
    state=0x02600260 ^ (((r+1)*0x9E3779B9)&MASK32) ^ (((d+1)*0x85EBCA6B)&MASK32)
    seed=state
    used=set(TRIPLES)
    clauses=[]
    while len(clauses)<d:
        triple=[]
        for _ in range(3):
            state=rng(state)
            triple.append(state%64+1)
        triple=tuple(sorted(triple))
        if len(set(triple))!=3 or triple in used:
            continue
        used.add(triple)
        clause=[]
        for v in triple:
            state=rng(state)
            clause.append(-v if (state&1) else v)
        if not any(planted(l) for l in clause):
            clause[0]=-clause[0]
        assert any(planted(l) for l in clause)
        clauses.append(clause)
    return seed,clauses

def fingerprint(clauses):
    h=0xcbf29ce484222325
    for clause in clauses:
        for literal in clause:
            h ^= literal+64
            h=(h*0x100000001b3)&MASK64
    return str(h)

def extract(clauses):
    groups=collections.defaultdict(list)
    for clause in clauses:
        key=tuple(sorted(abs(x) for x in clause))
        assert len(set(key))==3
        signs=tuple(1 if next(x for x in clause if abs(x)==v)>0 else -1 for v in key)
        groups[key].append(signs)
    rows=[]
    for key,patterns in sorted(groups.items()):
        if len(patterns)!=4 or len(set(patterns))!=4:
            continue
        prod=[a*b*c for a,b,c in patterns]
        if len(set(prod))!=1:
            continue
        rows.append((sum(1<<(v-1) for v in key),int(prod[0]>0)))
    return len(groups),rows

def inconsistent(rows):
    for subset in range(1,1<<len(rows)):
        mask=0
        rhs=0
        for j,(m,b) in enumerate(rows):
            if (subset>>j)&1:
                mask ^= m
                rhs ^= b
        if mask==0 and rhs==1:
            return True
    return False

class W026IndependentTest(unittest.TestCase):
    def test_all_96_cases_against_source(self):
        exe=os.environ.get("WITNORA_RUST_MIXED_BIN")
        self.assertTrue(exe and os.path.isfile(exe),"set WITNORA_RUST_MIXED_BIN")
        result=subprocess.run([exe,"--json"],capture_output=True,text=True,check=True)
        data=json.loads(result.stdout)
        self.assertEqual(data["study"],"W-CROSSDOMAIN-026")
        self.assertEqual(data["case_count"],96)
        self.assertEqual(data["noise_sizes"],list(SIZES))
        self.assertEqual(len(data["cases"]),96)
        for i,case in enumerate(data["cases"]):
            d,r=SIZES[i//16],i%16
            with self.subTest(noise=d,replicate=r):
                self.assertEqual((case["noise"],case["replicate"]),(d,r))
                seed,noise=make_noise(d,r)
                self.assertEqual(case["seed"],seed)
                self.assertEqual(case["noise_fingerprint_fnv64"],fingerprint(noise))
                self.assertEqual(case["first_four_noise_clauses"],noise[:4])
                self.assertEqual(case["literal_clauses_each"],d+20)
                self.assertEqual(case["supports_indexed"],d+5)
                self.assertEqual(case["one_pass_clause_visits"],d+20)
                self.assertEqual(case["cached_initial_clause_visits"],d+20)
                for q in (1,2,8,32):
                    self.assertEqual(case["rescan_clause_visits_q"+str(q)],q*(d+20))
                if d in (0,256,8192) and r in (0,1,15):
                    for rhs,should_contradict in ((SAT,False),(UNSAT,True)):
                        cnf=core(rhs)+noise
                        self.assertEqual(len(cnf),d+20)
                        supports,rows=extract(cnf)
                        self.assertEqual((supports,len(rows)),(d+5,5))
                        self.assertEqual(inconsistent(rows),should_contradict)
                        if not should_contradict:
                            self.assertTrue(all(any(planted(l) for l in c) for c in cnf))
                self.assertEqual(case["recovered_exact_xor_blocks_sat"],5)
                self.assertEqual(case["recovered_exact_xor_blocks_unsat"],5)
                self.assertTrue(case["sat_planted_witness_valid"])
                self.assertTrue(case["unsat_xor_contradiction"])
                self.assertTrue(case["sat_xor_consistent"])

if __name__=="__main__":
    unittest.main()
