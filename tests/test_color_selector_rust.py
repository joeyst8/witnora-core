"""R-102: exact selector features and frozen rule decisions in Rust."""
import random
import unittest
from itertools import combinations

from witnora_core.color_selector_lab import RULES, signals, triggers
from witnora_core.nonedge_matching_bound import _dsatur_greedy_coloring


class ColorSelectorRustTests(unittest.TestCase):
    def test_seeded_features_and_all_rules(self):
        rng = random.Random(20261109)
        for trial in range(270):
            n = rng.randrange(0, 17)
            p = rng.choice((0.05, 0.25, 0.50, 0.75, 0.95))
            edges = tuple((u, v) for u, v in combinations(range(n), 2)
                          if rng.random() < p)
            colors = _dsatur_greedy_coloring(n, edges)["coloring"] if n else []
            if trial % 13 == 0:
                colors = [c + 2 for c in colors]
            with self.subTest(trial=trial, n=n):
                pfeatures = signals(n, edges, colors)
                rfeatures = signals(n, edges, colors, backend="rust")
                self.assertEqual(rfeatures, pfeatures)
                for rule in RULES:
                    self.assertEqual(triggers(rule, pfeatures, backend="rust"),
                                     triggers(rule, pfeatures), rule)

    def test_unknown_selector(self):
        features = signals(3, ((0, 1),), [0, 1, 0])
        for backend in ("python", "rust"):
            with self.assertRaises(ValueError):
                triggers("not-a-selector", features, backend=backend)


if __name__ == "__main__":
    unittest.main()
