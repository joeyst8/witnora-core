"""Independent W019 generator and exact covariance/XOR proof replay."""

from __future__ import annotations

import json
import os
import subprocess
import unittest

from tests.test_signed_covariance_rust import covariance_matrix, next_random
from tests.test_zero_variance_refutation_rust import violated, models

BIN = os.environ.get("WITNORA_RUST_HYBRID_REFUTATION_BIN")
MASK = (1 << 32)-1
SEEDS = {
    "fresh_planted_sat_48": 0xD19C0DE1,
    "fresh_uniform_boundary_48": 0xD19C0DE2,
    "hidden_eight_core_unsat_56": 0xD19C0DE3,
    "hidden_parity_cycle_unsat_64": 0xD19C0DE4,
}
PARITY = [((1,2,3),0),((1,4,5),0),((2,4,6),0),((3,5,6),1)]


def source(name: str, index: int) -> list[list[int]]:
    state = SEEDS[name] ^ (((index+1)*0x9E3779B9)&MASK)
    clauses: list[list[int]] = []
    if name == "hidden_eight_core_unsat_56":
        for bits in range(8):
            clauses.append([-v if bits&(1<<(v-1)) else v for v in (1,2,3)])
    if name == "hidden_parity_cycle_unsat_64":
        for triple, rhs in PARITY:
            for bits in range(8):
                if bits.bit_count()%2 == rhs:
                    continue
                clauses.append([-v if bits&(1<<j) else v
                                for j,v in enumerate(triple)])
    target = 56 if name == "hidden_eight_core_unsat_56" else (
        64 if name == "hidden_parity_cycle_unsat_64" else 48)
    while len(clauses) < target:
        seen = set()
        clause = []
        while len(clause) < 3:
            state = next_random(state)
            v = 1 + state%12
            if v in seen:
                continue
            seen.add(v)
            state = next_random(state)
            clause.append(-v if state&1 else v)
        if name == "fresh_planted_sat_48" and all(lit>0 for lit in clause):
            continue
        clauses.append(clause)
    permutation = list(range(1,13))
    for i in range(11,0,-1):
        state = next_random(state)
        j = state%(i+1)
        permutation[i],permutation[j] = permutation[j],permutation[i]
    flips = []
    for _ in range(12):
        state = next_random(state)
        flips.append(bool(state&1))
    clauses = [[(-1 if (lit<0)^flips[abs(lit)-1] else 1)
                *permutation[abs(lit)-1] for lit in clause] for clause in clauses]
    for i in range(len(clauses)-1,0,-1):
        state = next_random(state)
        j = state%(i+1)
        clauses[i],clauses[j] = clauses[j],clauses[i]
    return clauses


def verify_xor(clauses: list[list[int]], equations: list[dict]) -> None:
    assert equations, "empty parity certificate"
    mask=rhs=0
    for eq in equations:
        triple=eq["variables"]
        assert len(triple)==3 and len(set(triple))==3
        assert triple==sorted(triple)
        assert eq["rhs"] in (0,1)
        assert len(eq["clause_indices"])==4
        patterns=set()
        for i in eq["clause_indices"]:
            clause=clauses[i]
            assert sorted(abs(lit) for lit in clause)==triple
            pattern=sum((1<<j) for j,v in enumerate(triple) if -v in clause)
            patterns.add(pattern)
        forbidden={p for p in range(8) if p.bit_count()%2!=eq["rhs"]}
        assert patterns==forbidden
        for v in triple:
            mask^=1<<(v-1)
        rhs^=eq["rhs"]
    assert mask==0 and rhs==1, "rows do not contradict"


@unittest.skipUnless(BIN,"compiled W019 Rust executable unavailable")
class HybridRefutationIndependentOracle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(subprocess.run([BIN],check=True,capture_output=True,
                                             text=True,timeout=300).stdout)

    def test_frozen_families_counts(self):
        self.assertEqual(self.report["research_id"],"W-CROSSDOMAIN-019")
        self.assertEqual({f["family"] for f in self.report["families"]},set(SEEDS))
        for family in self.report["families"]:
            with self.subTest(family=family["family"]):
                self.assertEqual(family["formulas"],32)
                self.assertEqual(family["satisfiable"]+family["unsatisfiable"],32)
                self.assertEqual(family["covariance_proofs"]+family["xor_proofs"]
                                 +family["no_certificate"],32)
                self.assertLessEqual(family["covariance_proofs"]+family["xor_proofs"],
                                     family["unsatisfiable"])
                self.assertEqual([x["index"] for x in family["controls"]],[0,1,31])
                if family["family"]=="fresh_planted_sat_48":
                    self.assertEqual(family["satisfiable"],32)
                    self.assertEqual(family["covariance_proofs"]+family["xor_proofs"],0)
                if family["family"]=="hidden_eight_core_unsat_56":
                    self.assertEqual((family["unsatisfiable"],family["covariance_proofs"]),
                                     (32,32))
                if family["family"]=="hidden_parity_cycle_unsat_64":
                    self.assertEqual((family["unsatisfiable"],family["xor_proofs"]),(32,32))

    def test_source_truth_and_exact_replay_controls(self):
        for family in self.report["families"]:
            for control in family["controls"]:
                with self.subTest(family=family["family"],index=control["index"]):
                    clauses=source(family["family"],control["index"])
                    self.assertEqual(clauses,control["source"])
                    self.assertEqual(models(clauses),control["models"])
                    proof=control["proof"]
                    if proof["kind"]=="none":
                        continue
                    self.assertEqual(control["models"],0)
                    if proof["kind"]=="xor":
                        verify_xor(clauses,proof["equations"])
                    elif proof["kind"]=="covariance":
                        weights=[int(v) for v in proof["weights"]]
                        self.assertEqual(len(weights),len(clauses))
                        self.assertNotEqual(sum(weights),0)
                        matrix=covariance_matrix(clauses)
                        self.assertTrue(all(sum(a*b for a,b in zip(row,weights))==0
                                            for row in matrix))
                        self.assertEqual(sum(weights)%8,0)
                        for assignment in range(1<<12):
                            energy=sum(w for c,w in zip(clauses,weights)
                                       if violated(c,assignment))
                            self.assertEqual(energy,sum(weights)//8)
                    else:
                        self.fail(f"unknown proof type {proof['kind']}")


if __name__=="__main__":
    unittest.main()
