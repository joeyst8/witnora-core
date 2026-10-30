"""Fail-closed paired comparison tests for lookahead failure analysis."""
import unittest

from scripts.analyze_lookahead_failures import analyze


def row(strategy, gain, elapsed, *, agreement=True):
    return {
        "seed": "613", "family": "pigeonhole", "case_id": "php_5_into_4",
        "strategy": strategy, "structural_gain": str(gain),
        "total_ms": str(elapsed),
        "independent_solver_agreement": str(agreement),
        "source_sha256": "fixed-example",
    }


class LookaheadFailureTests(unittest.TestCase):
    def test_detects_slowdown_despite_structural_gain(self):
        data = [row("greedy_two_steps", 3, 1),
                row("speculative_two_ply", 4, 5)]
        report = analyze(data)
        self.assertEqual(report["structural_losses"], 0)
        self.assertEqual(report["runtime_slowdowns"], 1)
        self.assertFalse(report["candidate_proven_faster"])

    def test_detects_structural_regression(self):
        data = [row("greedy_two_steps", 5, 7),
                row("speculative_two_ply", 3, 6)]
        self.assertEqual(analyze(data)["structural_losses"], 1)

    def test_rejects_missing_or_unchecked_pairs(self):
        with self.assertRaises(ValueError):
            analyze([row("greedy_two_steps", 1, 1)])
        with self.assertRaises(ValueError):
            analyze([row("greedy_two_steps", 1, 1),
                     row("speculative_two_ply", 1, 1, agreement=False)])


if __name__ == "__main__":
    unittest.main()
