"""Independent W018 source, matrix, assignment and integer-witness oracle."""

from __future__ import annotations

import json
import os
import subprocess
import unittest

from tests.test_signed_covariance_rust import covariance_matrix, next_random

BIN = os.environ.get("WITNORA_RUST_ZERO_VARIANCE_BIN")
MASK = (1 << 32) - 1
SEEDS = {
    "fresh_planted_sat_48": 0xD18C0DE1,
    "fresh_uniform_boundary_48": 0xD18C0DE2,
    "eight_pattern_embedded_unsat_56": 0xD18C0DE3,
    "four_xor_cycle_unsat_64": 0xD18C0DE4,
}
XOR_EQUATIONS = [((1, 2, 3), 0), ((1, 4, 5), 0),
                 ((2, 4, 6), 0), ((3, 5, 6), 1)]


def source(name: str, index: int) -> list[list[int]]:
    state = (SEEDS[name] ^ ((index + 1) * 0x9E3779B9 & MASK)) & MASK
    clauses: list[list[int]] = []
    if name == "eight_pattern_embedded_unsat_56":
        clauses.extend([[-v if pattern & (1 << (v - 1)) else v
                        for v in (1, 2, 3)] for pattern in range(8)])
    if name == "four_xor_cycle_unsat_64":
        for variables, desired in XOR_EQUATIONS:
            for bits in range(8):
                if (bits.bit_count() & 1) == desired:
                    continue
                clauses.append([-v if bits & (1 << j) else v
                                for j, v in enumerate(variables)])
    goal = 56 if name == "eight_pattern_embedded_unsat_56" else (
        64 if name == "four_xor_cycle_unsat_64" else 48)
    while len(clauses) < goal:
        clause: list[int] = []
        seen: set[int] = set()
        while len(clause) < 3:
            state = next_random(state)
            variable = 1 + state % 12
            if variable in seen:
                continue
            seen.add(variable)
            state = next_random(state)
            clause.append(-variable if state & 1 else variable)
        if name == "fresh_planted_sat_48" and all(lit > 0 for lit in clause):
            continue
        clauses.append(clause)
    return clauses


def violated(clause: list[int], assignment: int) -> bool:
    return not any(bool(assignment & (1 << (abs(lit)-1))) == (lit > 0)
                   for lit in clause)


def models(clauses: list[list[int]]) -> int:
    return sum(not any(violated(clause, x) for clause in clauses)
               for x in range(1 << 12))


@unittest.skipUnless(BIN, "compiled W018 Rust executable unavailable")
class ZeroVarianceIndependentOracle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(subprocess.run([BIN], check=True, capture_output=True,
                                               text=True, timeout=300).stdout)

    def test_predeclared_population_and_soundness(self):
        self.assertEqual(self.report["research_id"], "W-CROSSDOMAIN-018")
        self.assertEqual({x["family"] for x in self.report["families"]}, set(SEEDS))
        for family in self.report["families"]:
            with self.subTest(family=family["family"]):
                self.assertEqual(family["formulas"], 32)
                self.assertEqual(family["satisfiable"] + family["unsatisfiable"], 32)
                self.assertLessEqual(family["certificates"], family["unsatisfiable"])
                self.assertEqual([x["index"] for x in family["controls"]], [0, 1, 31])
                if family["family"] == "fresh_planted_sat_48":
                    self.assertEqual((family["satisfiable"],family["certificates"]), (32, 0))
                if family["family"] == "eight_pattern_embedded_unsat_56":
                    self.assertEqual((family["unsatisfiable"],family["certificates"]), (32, 32))
                if family["family"] == "four_xor_cycle_unsat_64":
                    self.assertEqual(family["unsatisfiable"], 32)

    def test_independent_exact_witness_verification(self):
        for family in self.report["families"]:
            for control in family["controls"]:
                with self.subTest(family=family["family"],index=control["index"]):
                    clauses = source(family["family"],control["index"])
                    self.assertEqual(clauses,control["source"])
                    self.assertEqual(models(clauses),control["models"])
                    k = covariance_matrix(clauses)
                    self.assertEqual(control["covariance_top_left_8"],
                                     [row[:8] for row in k[:8]])
                    witness = control["integer_nullspace_witness"]
                    if witness is None:
                        continue  # This sufficient method may miss UNSAT.
                    weights = [int(v) for v in witness]
                    self.assertEqual(len(weights),len(clauses))
                    self.assertNotEqual(sum(weights),0)
                    self.assertEqual(control["models"],0)
                    self.assertTrue(all(sum(a * b for a,b in zip(row,weights)) == 0
                                        for row in k))
                    self.assertEqual(sum(weights) % 8,0)
                    for assignment in range(1 << 12):
                        weighted_energy = sum(w for c,w in zip(clauses,weights)
                                              if violated(c,assignment))
                        self.assertEqual(weighted_energy,sum(weights) // 8)


if __name__ == "__main__":
    unittest.main()
