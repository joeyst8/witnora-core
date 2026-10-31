"""Deterministic signal extraction and selector constraint checks."""
import unittest

from witnora_core.color_selector_lab import signals, triggers, confusion, RULES
from witnora_core.structured_coloring_study import greedy_clique_lower_bound


class ColorSelectorTests(unittest.TestCase):
    def test_clique_certificate_forces_no_repair(self):
        edges = ((0, 1), (0, 2), (1, 2))
        feat = signals(3, edges, [0, 1, 2])
        self.assertEqual(feat["gap"], 0)
        for rule in RULES:
            self.assertFalse(triggers(rule, feat))

    def test_known_noncertified_signals(self):
        feat = signals(3, ((0, 1),), [0, 1, 2])
        self.assertEqual(feat["gap"], 1)
        self.assertTrue(triggers("uncertified", feat))
        self.assertFalse(triggers("gap_ge_2", feat))
        self.assertEqual(greedy_clique_lower_bound(3, ((0, 1),)), 2)

    def test_confusion_counts(self):
        feat = {"gap": 1, "last_size": 1, "min_class": 1,
                "singleton": 1, "k": 4, "clique": 3}
        rows = [{"signals": feat, "failure": True},
                {"signals": {**feat, "gap": 0}, "failure": False}]
        measured = confusion(rows, "uncertified")
        self.assertEqual(measured["selected"], 1)
        self.assertEqual(measured["true_positives"], 1)


if __name__ == "__main__":
    unittest.main()
