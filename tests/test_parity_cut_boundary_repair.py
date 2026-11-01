"""Correctness and scientific-control tests for boundary repair."""
import unittest

from witnora_core.hidden_separator_challenge import (
    make_hidden_separator, full_cnf_anchors_separated,
)
from witnora_core.parity_cut_boundary_repair import (
    repair_parity_separator, independent_minimum_anchor_cut,
)
from scripts.experiment_parity_cut_boundary_repair import run_experiment


class ParityCutBoundaryRepairTests(unittest.TestCase):
    def test_clean_candidate_needs_no_repair(self):
        formula, m = make_hidden_separator(4, width=2, cross_noise=False)
        r = repair_parity_separator(
            formula, m["boundary"], m["left_anchor"], m["right_anchor"]
        )
        self.assertEqual(r["status"], "ALREADY_SOUND")
        self.assertEqual(r["extra_variables"], [])

    def test_nonxor_cross_clause_requires_repair(self):
        formula, m = make_hidden_separator(4, width=2, cross_noise=True)
        self.assertFalse(full_cnf_anchors_separated(
            formula, m["boundary"], m["left_anchor"], m["right_anchor"]
        ))
        r = repair_parity_separator(
            formula, m["boundary"], m["left_anchor"], m["right_anchor"]
        )
        self.assertEqual(r["status"], "REPAIRED")
        self.assertTrue(r["extra_variables"])
        self.assertTrue(full_cnf_anchors_separated(
            formula, tuple(r["repaired_cut"]),
            m["left_anchor"], m["right_anchor"]
        ))
        optimum = independent_minimum_anchor_cut(
            formula, m["left_anchor"], m["right_anchor"]
        )
        self.assertIsNotNone(optimum)
        self.assertLessEqual(len(optimum), len(r["repaired_cut"]))

    def test_trial_cap_fails_closed(self):
        formula, m = make_hidden_separator(4, width=2, cross_noise=True)
        r = repair_parity_separator(
            formula, m["boundary"], m["left_anchor"], m["right_anchor"],
            max_trials=1
        )
        self.assertEqual(r["status"], "BUDGET_EXHAUSTED")
        self.assertFalse(r["full_cnf_separated"])

    def test_study_is_deterministic_and_not_vacuous(self):
        a = run_experiment(range(2))
        self.assertEqual(a, run_experiment(range(2)))
        self.assertEqual(a["summary"]["cases"], 8)
        self.assertGreater(a["summary"]["needed_extra"], 0)
        self.assertFalse(a["summary"]["novelty_established"])


if __name__ == "__main__":
    unittest.main()
