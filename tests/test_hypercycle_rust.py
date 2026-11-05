"""Independent GF(2) incidence-kernel and DPLL oracle for Rust W-013."""

from __future__ import annotations

from itertools import permutations
import json
import os
import subprocess
import unittest

from tests.test_three_cnf_geometry_rust import independent_dpll, signed_source


BIN = os.environ.get("WITNORA_RUST_HYPERCYCLE_BIN")

FROZEN = {
    "P1_Pasch_offset": [(1, 2, 3), (1, 4, 5), (2, 4, 6),
                        (3, 5, 6), (1, 2, 4), (3, 4, 5)],
    "P2_Pasch_shared_vertices": [(1, 2, 3), (1, 4, 5), (2, 4, 6),
                                 (3, 5, 6), (1, 2, 4), (1, 2, 5)],
}
OLD_T2 = [(1, 2, 3), (1, 2, 4), (1, 3, 5),
          (1, 4, 6), (2, 3, 5), (4, 5, 6)]


def even_incidence_selector(scopes: list[tuple[int, int, int]]) -> list[int]:
    """Independent set-symmetric-difference oracle, not Rust bitset code."""
    candidates = []
    for mask in range(1, 1 << len(scopes)):
        indices = [i for i in range(len(scopes)) if mask & (1 << i)]
        odd = set()
        for index in indices:
            odd.symmetric_difference_update(scopes[index])
        if not odd:
            candidates.append((len(indices), mask, indices))
    return min(candidates)[2]


def truth_table(clauses: list[list[int]], parity_indices: list[int]) -> tuple[list[int], list[int]]:
    energy = [0] * 7
    even = [0] * 7
    for assignment in range(64):
        violated = [index for index, clause in enumerate(clauses)
                    if not any(bool(assignment & (1 << (abs(lit) - 1))) == (lit > 0)
                               for lit in clause)]
        weight = len(violated)
        energy[weight] += 1
        if len(set(violated) & set(parity_indices)) % 2 == 0:
            even[weight] += 1
    return energy, even


def isomorphic(source, target) -> bool:
    target_set = {frozenset(clause) for clause in target}
    for permutation in permutations(range(1, 7)):
        renamed = {frozenset(permutation[vertex - 1] for vertex in clause)
                   for clause in source}
        if renamed == target_set:
            return True
    return False


@unittest.skipUnless(BIN is not None, "compiled Rust W-013 CLI unavailable")
class RustHypercycleIndependentOracle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(subprocess.run([BIN], check=True, capture_output=True,
                                               text=True, timeout=180).stdout)

    def test_predeclared_selector_and_strict_criterion(self):
        report = self.report
        self.assertEqual(report["research_id"], "W-CROSSDOMAIN-013")
        families = report["families"]
        self.assertEqual({f["graph_name"] for f in families}, set(FROZEN))
        strict = True
        degree_profiles = set()
        for family in families:
            name = family["graph_name"]
            scopes = FROZEN[name]
            self.assertEqual(family["source_scopes_one_based"],
                             [list(clause) for clause in scopes])
            selected = even_incidence_selector(scopes)
            self.assertEqual(selected, family["chosen_parity_indices"])
            self.assertEqual(selected, [0, 1, 2, 3])
            self.assertEqual(family["signings"], 262144)
            self.assertEqual(family["gauge_representatives"], 4096)
            self.assertGreaterEqual(family["minimum_model_count"], 16)
            degree_profiles.add(tuple(sorted(sum(v in clause for clause in scopes)
                                             for v in range(1, 7))))
            for direction in ("forward", "reverse"):
                data = family[direction]
                self.assertGreater(data["samples"], 0)
                self.assertEqual(data["permutations"], 1000)
                if not data["baseline_zero"]:
                    self.assertAlmostEqual(data["improvement_fraction"],
                                           1 - data["syndrome_loo_mse"] /
                                           data["baseline_loo_mse"])
                strict &= data["improvement_fraction"] is not None
                strict &= data["improvement_fraction"] is not None and data["improvement_fraction"] > 0
                strict &= data["exploratory_permutation_p"] <= 0.0125
                self.assertTrue(0 <= family[direction + "_work"]
                                ["feature_scans_exceed_dpll_fraction"] <= 1)
        self.assertEqual(len(degree_profiles), 2)
        self.assertFalse(isomorphic(FROZEN["P1_Pasch_offset"], OLD_T2))
        self.assertEqual(report["strict_four_way_replication_met"], strict)

    def test_each_reference_signing_independent_literal_and_dpll_oracles(self):
        for family in self.report["families"]:
            scopes = FROZEN[family["graph_name"]]
            indices = family["chosen_parity_indices"]
            for row in family["controls"]:
                with self.subTest(graph=family["graph_name"], mask=row["mask"]):
                    clauses = signed_source(scopes, row["mask"])
                    self.assertEqual(row["source"], clauses)
                    energy, parity_even = truth_table(clauses, indices)
                    self.assertEqual(row["energy"], energy)
                    self.assertEqual(row["alternate_even"], parity_even)
                    for direction, order in (("forward", tuple(range(6))),
                                             ("reverse", tuple(reversed(range(6))))):
                        self.assertEqual(row[direction], independent_dpll(clauses, order))


if __name__ == "__main__":
    unittest.main()
