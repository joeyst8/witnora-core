"""R-106: frozen selector confusion counts including zero denominators."""
import random
import unittest

from witnora_core.color_selector_lab import RULES, confusion


class ColorConfusionRustTests(unittest.TestCase):
    def test_seeded_differential(self):
        rng = random.Random(20261113)
        for trial in range(90):
            rows = []
            for _ in range(rng.randrange(0, 40)):
                k = rng.randrange(0, 7)
                gap = rng.randrange(-2, 5)
                rows.append({"failure": bool(rng.randrange(2)),
                             "signals": {"k": k, "gap": gap,
                                         "last_size": rng.randrange(0, 5),
                                         "min_class": rng.randrange(0, 5),
                                         "singleton": rng.randrange(0, 5)}})
            for rule in RULES:
                with self.subTest(trial=trial, rule=rule):
                    self.assertEqual(confusion(rows, rule, backend="rust"),
                                     confusion(rows, rule))


if __name__ == "__main__":
    unittest.main()
