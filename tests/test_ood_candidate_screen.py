"""Reject false discovery claims from out-of-distribution screens."""
import unittest

from scripts.screen_ood_candidates import screen


def case(family, gain, agree="1", sequence="a+b"):
    return {
        "test_category": "frozen_holdout",
        "sequence": sequence,
        "family": family,
        "interaction_gain": str(gain),
        "glucose3_and_minisat22_agree": agree,
        "complete_experimental_ms": "2.0",
        "source_glucose3_median_ms": "1.0",
    }


class ScreenTest(unittest.TestCase):
    def test_good_structural_candidate_is_still_unverified(self):
        records = [case(family, 2) for family in ("A", "B", "C", "D")]
        row = screen(records)[0]
        self.assertTrue(row["followup_recommended"])
        self.assertFalse(row["promoted"])
        self.assertFalse(row["lean_verified"])
        self.assertFalse(row["novelty_verified"])
        self.assertFalse(row["performance_advantage_verified"])

    def test_single_family_win_not_generalization(self):
        records = [case("A", 5), case("B", 0), case("C", -2)]
        row = screen(records)[0]
        self.assertFalse(row["followup_recommended"])
        self.assertEqual(row["no_gain_or_negative_cases"], 2)

    def test_oracle_mismatch_fails_closed(self):
        with self.assertRaises(ValueError):
            screen([case("A", 100, agree="0")])


if __name__ == "__main__":
    unittest.main()
