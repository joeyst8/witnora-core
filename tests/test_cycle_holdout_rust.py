"""Independent source reconstruction for the frozen W-CROSSDOMAIN-011 graphs."""

from __future__ import annotations

import json
import os
import subprocess
import unittest

from tests.test_cycle_cost_audit_rust import independent_spectra, reference_cost


BIN = os.environ.get("WITNORA_RUST_CYCLE_HOLDOUT_BIN")

FROZEN_GRAPHS = {
    "H1_double_triangle_tail": [(1, 2), (1, 3), (1, 4), (2, 3),
                                (2, 4), (3, 5), (5, 6)],
    "H2_two_leaves": [(1, 2), (1, 3), (1, 4), (2, 3),
                      (2, 5), (2, 6), (3, 4)],
}


@unittest.skipUnless(BIN is not None, "compiled Rust cycle-holdout CLI unavailable")
class RustGraphHoldoutIndependentOracle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(subprocess.run([BIN], check=True, capture_output=True,
                                               text=True, timeout=120).stdout)

    def test_frozen_graphs_and_recomputed_strict_criterion(self):
        report = self.report
        self.assertEqual(report["research_id"], "W-CROSSDOMAIN-011")
        self.assertEqual(report["original"]["research_id"], "W-CROSSDOMAIN-010")
        families = report["holdouts"]
        self.assertEqual(len(families), 2)
        self.assertEqual({family["graph_name"] for family in families}, set(FROZEN_GRAPHS))
        strict = True
        degrees = set()
        for family in families:
            self.assertEqual(family["graph_edges_one_based"],
                             [list(pair) for pair in FROZEN_GRAPHS[family["graph_name"]]])
            self.assertEqual(family["triangle_clause_indices"], [0, 1, 3])
            self.assertEqual(family["signings"], 16384)
            self.assertEqual(family["gauge_representatives"], 256)
            counts = [0] * 6
            for u, v in FROZEN_GRAPHS[family["graph_name"]]:
                counts[u - 1] += 1
                counts[v - 1] += 1
            degrees.add(tuple(sorted(counts)))
            for direction in ("forward", "reverse"):
                stat = family[direction]
                self.assertGreater(stat["samples"], 0)
                self.assertEqual(stat["permutation_replicates"], 1000)
                self.assertAlmostEqual(stat["mse_improvement_fraction"],
                                       1 - stat["spectrum_loo_mse"] / stat["baseline_loo_mse"])
                strict &= stat["mse_improvement_fraction"] > 0
                strict &= stat["exploratory_permutation_p"] <= 0.0125
        self.assertEqual(len(degrees), 2)
        self.assertEqual(report["strict_four_way_replication_met"], strict)

    def test_every_control_source_and_dpll_result_independently(self):
        for family in self.report["holdouts"]:
            edges = FROZEN_GRAPHS[family["graph_name"]]
            for row in family["controls"]:
                with self.subTest(graph=family["graph_name"], mask=row["mask"]):
                    clauses = []
                    for index, (left, right) in enumerate(edges):
                        mask = row["mask"]
                        clauses.append([-left if mask & (1 << (2 * index)) else left,
                                        -right if mask & (1 << (2 * index + 1)) else right])
                    self.assertEqual(row["source"], clauses)
                    weight, even = independent_spectra(clauses)
                    self.assertEqual(row["energy"], weight)
                    self.assertEqual(row["triangle_even"], even)
                    for order, field in ((tuple(range(6)), "forward_nodes"),
                                         (tuple(reversed(range(6))), "reverse_nodes")):
                        nodes, models = reference_cost(clauses, order)
                        self.assertEqual(row[field], nodes)
                        self.assertEqual(row["energy"][0], models)


if __name__ == "__main__":
    unittest.main()
