"""Independent finite literal/branch oracle for Rust W-CROSSDOMAIN-010 CLI."""

from __future__ import annotations

import json
import os
import subprocess
import unittest


BIN = os.environ.get("WITNORA_RUST_CYCLE_COST_BIN")


def reference_cost(clauses: list[list[int]], order: tuple[int, ...]) -> tuple[int, int]:
    """Full DPLL model counter, with fixed-point unit propagation (0-based order)."""
    visits = 0

    def search(values: tuple[int | None, ...]) -> int:
        nonlocal visits
        visits += 1
        current = list(values)
        while True:
            changed = False
            for clause in clauses:
                truth = [current[abs(lit) - 1] is not None
                         and current[abs(lit) - 1] == (lit > 0)
                         for lit in clause]
                if any(truth):
                    continue
                free = [lit for lit in clause if current[abs(lit) - 1] is None]
                if not free:
                    return 0
                if len(free) == 1:
                    literal = free[0]
                    current[abs(literal) - 1] = literal > 0
                    changed = True
            if not changed:
                break
        if all(any(current[abs(lit) - 1] == (lit > 0)
                   for lit in clause) for clause in clauses):
            return 2 ** current.count(None)
        branch = next(index for index in order if current[index] is None)
        current[branch] = False
        left = search(tuple(current))
        current[branch] = True
        return left + search(tuple(current))

    models = search((None,) * 6)
    return visits, models


def independent_spectra(clauses: list[list[int]]) -> tuple[list[int], list[int]]:
    weights = [0] * 8
    even = [0] * 8
    for bits in range(64):
        unsat = [index for index, clause in enumerate(clauses)
                 if not any(bool(bits & (1 << (abs(lit) - 1))) == (lit > 0)
                            for lit in clause)]
        weights[len(unsat)] += 1
        if len({0, 1, 3}.intersection(unsat)) % 2 == 0:
            even[len(unsat)] += 1
    return weights, even


@unittest.skipUnless(BIN is not None, "compiled Rust cycle-cost CLI unavailable")
class RustCycleCostIndependentOracle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(subprocess.run([BIN], check=True, capture_output=True,
                                               text=True, timeout=120).stdout)

    def test_finite_orbit_and_exploratory_prediction_audit(self):
        report = self.report
        self.assertEqual(report["research_id"], "W-CROSSDOMAIN-010")
        self.assertEqual(report["signings"], 16384)
        self.assertEqual(report["gauge_representatives"], 256)
        self.assertEqual(report["energy_profiles"], 80)
        self.assertEqual(report["energy_plus_triangle_profiles"], 135)
        self.assertEqual(report["energy_groups_split_by_triangle"], 30)
        for order in ("forward", "reverse"):
            profile = report[order]
            self.assertEqual(profile["samples"], 243)
            self.assertEqual(profile["permutation_replicates"], 1000)
            self.assertGreater(profile["baseline_loo_mse"], 0)
            self.assertLess(profile["spectrum_loo_mse"], profile["baseline_loo_mse"])
            self.assertAlmostEqual(profile["mse_improvement_fraction"],
                                   1 - profile["spectrum_loo_mse"] /
                                   profile["baseline_loo_mse"])

    def test_source_literally_reconstructed_and_independent_dpll_counts(self):
        edges = [(1, 2), (1, 3), (1, 4), (2, 3), (2, 5), (4, 6), (5, 6)]
        for row in self.report["controls"]:
            with self.subTest(mask=row["mask"]):
                clauses = []
                for index, (left, right) in enumerate(edges):
                    clauses.append([-left if row["mask"] >> (2 * index) & 1 else left,
                                    -right if row["mask"] >> (2 * index + 1) & 1 else right])
                self.assertEqual(clauses, row["source"])
                weights, even = independent_spectra(clauses)
                self.assertEqual(weights, row["energy"])
                self.assertEqual(even, row["triangle_even"])
                for policy, expected in ((tuple(range(6)), "forward_nodes"),
                                         (tuple(reversed(range(6))), "reverse_nodes")):
                    nodes, models = reference_cost(clauses, policy)
                    self.assertEqual(nodes, row[expected])
                    self.assertEqual(models, row["energy"][0])


if __name__ == "__main__":
    unittest.main()
