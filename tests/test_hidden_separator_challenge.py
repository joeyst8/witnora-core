"""Blind detector-versus-independent graph and cross-edge controls."""
import unittest

from witnora_core.hidden_separator_challenge import (
    make_hidden_separator, independent_parity_cut_width, full_cnf_anchors_separated,
)
from witnora_core.multicut_parity_separator import bounded_parity_separators
from witnora_core.xor import detect_cnf_xor_patterns


class HiddenSeparatorChallengeTests(unittest.TestCase):
    def test_hidden_widths_and_cross_noise(self):
        for width in (2, 3):
            for cross_noise in (False, True):
                for seed in (11, 31, 47):
                    source, hidden = make_hidden_separator(
                        seed, width=width, cross_noise=cross_noise)
                    found = bounded_parity_separators(source)
                    supports = [tuple(eq.variables)
                                for eq in detect_cnf_xor_patterns(source).equations]
                    self.assertEqual(independent_parity_cut_width(supports), width)
                    self.assertEqual(found["smallest_cut_size"], width)
                    self.assertIn(list(hidden["boundary"]),
                                  [item["variables"] for item in found["candidate_cuts"]])
                    separated = full_cnf_anchors_separated(
                        source, hidden["boundary"],
                        hidden["left_anchor"], hidden["right_anchor"])
                    self.assertEqual(separated, not cross_noise)
                    self.assertFalse(found["full_cnf_separation_verified"])

    def test_repeatable_and_invalid_width(self):
        self.assertEqual(make_hidden_separator(29), make_hidden_separator(29))
        with self.assertRaises(ValueError):
            make_hidden_separator(29, width=4)


if __name__ == "__main__":
    unittest.main()
