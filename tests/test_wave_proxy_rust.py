"""Independent Python truth-table and DPLL controls for exploratory Rust W-014.

This does not classify the already-seen P1/P2 families as a held-out test.
"""

from __future__ import annotations

import json
import os
import subprocess
import unittest
from collections import Counter

from tests.test_hypercycle_rust import FROZEN, even_incidence_selector
from tests.test_three_cnf_geometry_rust import independent_dpll, signed_source


BIN = os.environ.get("WITNORA_RUST_WAVE_PROXY_BIN")


def exact_truth_table_character(source: list[list[int]], selected: list[int]) -> int:
    total = 0
    variables = max(abs(lit) for clause in source for lit in clause)
    for values in range(1 << variables):
        violations = 0
        for index in selected:
            clause = source[index]
            if not any(bool(values & (1 << (abs(lit) - 1))) == (lit > 0)
                       for lit in clause):
                violations += 1
        total += 1 if violations % 2 == 0 else -1
    return total


def independent_pair_conflicts(source: list[list[int]]) -> int:
    # Build each violation condition as a Python variable-to-value mapping,
    # independent of Rust's bitmask implementation.
    forbidden = [{abs(lit): lit < 0 for lit in clause} for clause in source]
    return sum(any(variable in forbidden[j] and forbidden[j][variable] != value
                   for variable, value in forbidden[i].items())
               for i in range(len(source)) for j in range(i + 1, len(source)))


@unittest.skipUnless(BIN is not None, "compiled Rust W-014 CLI unavailable")
class RustWaveProxyIndependentOracle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(subprocess.run([BIN], check=True, capture_output=True,
                                               text=True, timeout=240).stdout)

    def test_frozen_family_and_exploratory_statistics(self):
        self.assertEqual(self.report["research_id"], "W-CROSSDOMAIN-014")
        self.assertEqual({r["graph_name"] for r in self.report["families"]}, set(FROZEN))
        self.assertIn("exploratory", self.report["scope"])
        for family in self.report["families"]:
            self.assertEqual(family["gauge_representatives"], 4096)
            scopes = FROZEN[family["graph_name"]]
            self.assertEqual(family["chosen_parity_indices"],
                             even_incidence_selector(scopes))
            self.assertEqual(family["chosen_parity_indices"], [0, 1, 2, 3])
            # Independently reconstruct the 4096 gauge-canonical signings:
            # the first occurrence of each variable is positive, and the
            # remaining twelve incidence bits vary freely.
            first = {variable: min(3 * c + p for c, scope in enumerate(scopes)
                                   for p, v in enumerate(scope) if v == variable)
                     for variable in range(1, 7)}
            free_bits = [bit for bit in range(18) if bit not in set(first.values())]
            self.assertEqual(len(free_bits), 12)
            pair_counts = Counter()
            for setting in range(1 << len(free_bits)):
                mask = sum((1 << bit) for offset, bit in enumerate(free_bits)
                           if setting & (1 << offset))
                pair_counts[independent_pair_conflicts(signed_source(scopes, mask))] += 1
            expected_samples = sum(count for count in pair_counts.values() if count > 1)
            self.assertEqual(family["baseline_pair_conflict_groups"], len(pair_counts))
            self.assertEqual(family["excluded_singleton_baseline_rows"],
                             4096 - expected_samples)
            self.assertGreater(family["wave_bias_values"], 0)
            self.assertEqual(len(family["controls"]), 4)
            for order in ("forward", "reverse"):
                result = family[order]
                self.assertEqual(result["samples"], expected_samples)
                self.assertEqual(result["permutations"], 1000)
                self.assertTrue(0 < result["exploratory_permutation_p"] <= 1)
                self.assertGreaterEqual(result["baseline_loo_mse"], 0)
                self.assertGreaterEqual(result["wave_loo_mse"], 0)
                if result["baseline_loo_mse"] > 0:
                    self.assertAlmostEqual(result["improvement_fraction"],
                        1 - result["wave_loo_mse"] / result["baseline_loo_mse"])
                else:
                    self.assertIsNone(result["improvement_fraction"])
                work = family[order + "_work"]
                self.assertLessEqual(work["max_wave_selected_clause_visits"], 32)
                self.assertLessEqual(work["max_wave_literal_visits"], 96)
                self.assertTrue(0 <= work[
                    "wave_clause_visits_exceed_dpll_clause_scans_fraction"] <= 1)

    def test_all_control_signings_independent_oracles(self):
        for family in self.report["families"]:
            scopes = FROZEN[family["graph_name"]]
            row = family["chosen_parity_indices"]
            for control in family["controls"]:
                with self.subTest(graph=family["graph_name"], mask=control["mask"]):
                    source = signed_source(scopes, control["mask"])
                    self.assertEqual(control["source"], source)
                    wave = exact_truth_table_character(source, row)
                    self.assertEqual(control["wave_bias"], wave)
                    self.assertEqual(control["full_spectrum_bias"], wave)
                    self.assertEqual(control["pair_conflicts"],
                                     independent_pair_conflicts(source))
                    for name, order in (("forward", tuple(range(6))),
                                        ("reverse", tuple(range(5, -1, -1)))):
                        expected = independent_dpll(source, order)
                        self.assertEqual(control[name + "_nodes"], expected["nodes"])
                        self.assertEqual(control[name + "_clause_scans"],
                                         expected["clause_scans"])


if __name__ == "__main__":
    unittest.main()
