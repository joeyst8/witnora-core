"""Adversarial native tests; universal assurance comes only from Lean."""
from __future__ import annotations

from dataclasses import replace
import unittest

from scripts.generate_general_resolution_lean import (
    resolution_trace, small_truth, verify_steps,
)
from witnora_core.ood_sat_families import pigeonhole


class GeneralResolutionTests(unittest.TestCase):
    def test_non_affine_pigeonhole_resolution_refutation(self) -> None:
        raw = pigeonhole(3, 2).to_clause_lists()
        self.assertEqual(len(raw), 9)
        self.assertFalse(small_truth(raw))
        trace = resolution_trace(raw)
        self.assertGreater(len(trace), 10)
        self.assertTrue(verify_steps(raw, trace))

    def test_forged_last_step_and_pivot_are_rejected(self) -> None:
        raw = pigeonhole(3, 2).to_clause_lists()
        trace = resolution_trace(raw)
        self.assertFalse(verify_steps(raw, trace[:-1] + [
            replace(trace[-1], output=(1,))
        ]))
        self.assertFalse(verify_steps(raw, trace[:-1] + [
            replace(trace[-1], pivot=999)
        ]))

    def test_missing_source_clause_rejected(self) -> None:
        raw = pigeonhole(3, 2).to_clause_lists()
        trace = resolution_trace(raw)
        used_source = next(
            parent for step in trace for parent in (step.left, step.right)
            if parent in {tuple(row) for row in raw}
        )
        modified = [row for row in raw if tuple(row) != used_source]
        self.assertFalse(verify_steps(modified, trace))

    def test_sat_pigeonhole_has_no_resolution_refutation(self) -> None:
        raw = pigeonhole(2, 2).to_clause_lists()
        self.assertTrue(small_truth(raw))
        with self.assertRaises(ValueError):
            resolution_trace(raw)

    def test_invalid_literals_rejected(self) -> None:
        for bad in ([[0]], [[True]], [[1.2]]):
            with self.assertRaises(ValueError):
                resolution_trace(bad)


if __name__ == "__main__":
    unittest.main()
