"""Autonomous graph-separator discovery controls."""
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.autonomous_parity_separator import (
    discover_repaired_separator, full_cnf_groups_separated,
)
from witnora_core.hidden_separator_challenge import make_hidden_separator
from scripts.experiment_autonomous_parity_separator import run_experiment


class AutonomousParitySeparatorTests(unittest.TestCase):
    def test_full_group_audit_rejects_nonxor_bridge(self):
        formula, m = make_hidden_separator(3, width=2, cross_noise=True)
        left = set(m["left_block"])
        right = set(m["right_block"])
        # The exact XOR-variable groups are larger than the printed
        # anchor blocks; the existing cross-noise must still connect them.
        self.assertFalse(full_cnf_groups_separated(
            formula, m["boundary"], [left, right]))
        result = discover_repaired_separator(formula)
        if result["status"] == "FOUND":
            self.assertTrue(result["full_cnf_groups_separated"])

    def test_random_without_xor_pattern_fails_closed(self):
        formula = CNFFormula.from_raw_clauses(
            [[1, 2, 3], [-1, 4, 5], [2, -4, 6]]
        )
        result = discover_repaired_separator(formula)
        self.assertEqual(result["status"], "NO_AUDITED_CANDIDATE")
        self.assertFalse(result["full_cnf_groups_separated"])

    def test_work_budget_fails_closed(self):
        formula, _ = make_hidden_separator(2, width=2, cross_noise=True)
        result = discover_repaired_separator(formula, max_trials=1)
        self.assertNotEqual(result["status"], "FOUND")
        self.assertFalse(result["full_cnf_groups_separated"])

    def test_blind_study_reproducible(self):
        first = run_experiment(seed_count=2)
        self.assertEqual(first, run_experiment(seed_count=2))
        self.assertEqual(first["summary"]["total"], 12)
        self.assertTrue(first["summary"]["ground_truth_not_provided_to_detector"])


if __name__ == "__main__":
    unittest.main()
