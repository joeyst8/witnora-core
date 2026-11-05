"""R-140: the native DRAT byte count includes the trailing line feed."""
import random
import unittest

from witnora_core.xor_drat import _line_size


class XorDratLineSizeRustTests(unittest.TestCase):
    def test_seeded_sizes(self):
        rng = random.Random(140)
        for trial in range(200):
            clause = tuple(rng.sample(range(-10000, 10000), rng.randrange(0, 14)))
            with self.subTest(trial=trial):
                self.assertEqual(_line_size(clause, backend="rust"),
                                 _line_size(clause))


if __name__ == "__main__":
    unittest.main()
