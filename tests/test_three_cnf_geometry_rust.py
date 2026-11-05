"""Independent literal truth table and DPLL-work oracle for Rust W-012."""

from __future__ import annotations

import json
import os
import subprocess
import unittest


BIN = os.environ.get("WITNORA_RUST_THREE_CNF_BIN")

FROZEN = {
    "T1_cyclic_triple_overlap": [(1, 2, 3), (2, 3, 4), (3, 4, 5),
                                 (4, 5, 6), (5, 6, 1), (6, 1, 2)],
    "T2_skew_incidence": [(1, 2, 3), (1, 2, 4), (1, 3, 5),
                          (1, 4, 6), (2, 3, 5), (4, 5, 6)],
}


def signed_source(scopes: list[tuple[int, int, int]], mask: int) -> list[list[int]]:
    result = []
    for index, scope in enumerate(scopes):
        result.append([-variable if mask & (1 << (3 * index + offset)) else variable
                       for offset, variable in enumerate(scope)])
    return result


def source_truth_table(source: list[list[int]]) -> tuple[list[int], list[int], list[int]]:
    weights = [0] * 7
    alternate = [0] * 7
    all_even = [0] * 7
    for mask in range(64):
        violated = []
        for index, clause in enumerate(source):
            if not any(bool(mask & (1 << (abs(lit) - 1))) == (lit > 0)
                       for lit in clause):
                violated.append(index)
        count = len(violated)
        weights[count] += 1
        if len(set(violated) & {0, 2, 4}) % 2 == 0:
            alternate[count] += 1
        if count % 2 == 0:
            all_even[count] += 1
    return weights, alternate, all_even


def independent_dpll(source: list[list[int]], order: tuple[int, ...]) -> dict[str, int]:
    visits = 0
    clause_scans = 0

    def explore(values: tuple[bool | None, ...]) -> int:
        nonlocal visits, clause_scans
        visits += 1
        assignment = list(values)
        while True:
            changed = False
            for clause in source:
                clause_scans += 1
                if any(assignment[abs(lit) - 1] is not None
                       and assignment[abs(lit) - 1] == (lit > 0) for lit in clause):
                    continue
                unset = [lit for lit in clause if assignment[abs(lit) - 1] is None]
                if not unset:
                    return 0
                if len(unset) == 1:
                    lit = unset[0]
                    assignment[abs(lit) - 1] = lit > 0
                    changed = True
            if not changed:
                break
        all_satisfied = True
        for clause in source:
            clause_scans += 1
            if not any(assignment[abs(lit) - 1] is not None
                       and assignment[abs(lit) - 1] == (lit > 0) for lit in clause):
                all_satisfied = False
                break
        if all_satisfied:
            return 2 ** assignment.count(None)
        index = next(i for i in order if assignment[i] is None)
        assignment[index] = False
        left = explore(tuple(assignment))
        assignment[index] = True
        return left + explore(tuple(assignment))

    models = explore((None,) * 6)
    return {"nodes": visits, "models": models, "clause_scans": clause_scans}


@unittest.skipUnless(BIN is not None, "compiled Rust W-012 CLI unavailable")
class RustThreeCnfGeometryOracle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(subprocess.run([BIN], capture_output=True, check=True,
                                               text=True, timeout=180).stdout)

    def test_predeclared_exact_universe_and_strict_criterion_accounting(self):
        report = self.report
        self.assertEqual(report["research_id"], "W-CROSSDOMAIN-012")
        self.assertEqual(report["alternating_clause_indices"], [0, 2, 4])
        families = report["families"]
        self.assertEqual(len(families), 2)
        self.assertEqual({f["graph_name"] for f in families}, set(FROZEN))
        strict = True
        degree_sequences = set()
        for family in families:
            scopes = FROZEN[family["graph_name"]]
            self.assertEqual(family["source_scopes_one_based"],
                             [list(clause) for clause in scopes])
            self.assertEqual(family["signings"], 262144)
            self.assertEqual(family["gauge_representatives"], 4096)
            self.assertGreaterEqual(family["minimum_model_count"], 16)
            self.assertEqual(family["feature_clause_scans_per_formula"], 384)
            self.assertTrue(family["all_clauses_even_parity_is_energy_determined"])
            degree_sequences.add(tuple(sorted(sum(v in clause for clause in scopes)
                                              for v in range(1, 7))))
            for direction in ("forward", "reverse"):
                data = family[direction]
                self.assertEqual(data["permutations"], 1000)
                self.assertGreater(data["samples"], 0)
                if not data["baseline_zero"]:
                    self.assertAlmostEqual(data["improvement_fraction"],
                                           1 - data["syndrome_loo_mse"] /
                                           data["baseline_loo_mse"])
                else:
                    self.assertIsNone(data["improvement_fraction"])
                strict &= data["improvement_fraction"] is not None
                strict &= data["improvement_fraction"] is not None and data["improvement_fraction"] > 0
                strict &= data["exploratory_permutation_p"] <= 0.0125
                workload = family[direction + "_work"]
                self.assertGreaterEqual(workload["feature_scans_exceed_dpll_fraction"], 0)
                self.assertLessEqual(workload["feature_scans_exceed_dpll_fraction"], 1)
        self.assertEqual(len(degree_sequences), 2)
        self.assertEqual(report["strict_four_way_replication_met"], strict)

    def test_independent_source_truth_table_and_dpll_clause_scans(self):
        for family in self.report["families"]:
            scopes = FROZEN[family["graph_name"]]
            for row in family["controls"]:
                with self.subTest(graph=family["graph_name"], mask=row["mask"]):
                    source = signed_source(scopes, row["mask"])
                    self.assertEqual(row["source"], source)
                    energy, alternating, all_even = source_truth_table(source)
                    self.assertEqual(row["energy"], energy)
                    self.assertEqual(row["alternate_even"], alternating)
                    self.assertEqual(all_even,
                                     [value if degree % 2 == 0 else 0
                                      for degree, value in enumerate(energy)])
                    self.assertGreaterEqual(energy[0], 16)
                    for direction, order in (("forward", tuple(range(6))),
                                             ("reverse", tuple(reversed(range(6))))):
                        self.assertEqual(row[direction], independent_dpll(source, order))


if __name__ == "__main__":
    unittest.main()
