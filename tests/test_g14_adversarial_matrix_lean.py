"""Adversarial matrix reproducibility and non-vacuity tests."""
import unittest

from scripts.generate_g14_adversarial_matrix_lean import (
    CASES, emit_adversarial_matrix,
)


class G14AdversarialMatrixTests(unittest.TestCase):
    def test_cases_include_required_pathologies(self):
        names = {case[0] for case in CASES}
        self.assertTrue({
            "contradictory_units", "duplicate_clause",
            "separator_only_empty", "explicit_empty_clause",
            "two_separator_variables", "two_separator_contradiction",
        }.issubset(names))

    def test_real_python_results_are_deterministic(self):
        source, stats = emit_adversarial_matrix(16)
        self.assertEqual((source, stats), emit_adversarial_matrix(16))
        self.assertEqual(stats["cases"], len(CASES) + 16)
        self.assertGreaterEqual(stats["branches"], 40)
        self.assertGreater(stats["rejected_mutations"], 0)
        self.assertGreater(stats["normalized_duplicate_cases"], 0)
        self.assertIn("checkNormalizedPartition", source)
        self.assertIn("= false := by decide", source)
        self.assertNotIn("native_decide", source)
        self.assertNotIn("sorry", source)

    def test_unsupported_case_count_fails_closed(self):
        for count in (-1, 65):
            with self.assertRaises(ValueError):
                emit_adversarial_matrix(count)


if __name__ == "__main__":
    unittest.main()
