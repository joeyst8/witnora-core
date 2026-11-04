"""R-076 source-conditional independence exact native parity."""
import random
import unittest

from witnora_core.crc_conditional_independence import (
    audit_conditioned_source_independence as audit,
)


class ConditionalIndependenceRustTests(unittest.TestCase):
    def setUp(self):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            self.skipTest("native Rust wheel not installed")

    def check(self, *args):
        self.assertEqual(audit(*args, backend="rust"), audit(*args))

    def test_350_seeded_source_conditions(self):
        rng = random.Random(76076)
        for trial in range(350):
            n = rng.randrange(5, 17)
            boundary = tuple(range(1, n + 1))
            sep = tuple(v for v in range(5, n + 1) if rng.randrange(3)==0)
            rows = []
            for _ in range(rng.randrange(22)):
                chosen = rng.sample(boundary, rng.randrange(1, 5))
                signed = [v if rng.randrange(2) else -v for v in chosen]
                signed[0] = chosen[0]  # planted all-true source model
                rows.append(signed)
            witness = (1 << n) - 1
            with self.subTest(trial=trial):
                self.check(rows, boundary, (1, 2), (3, 4), sep, witness)
                self.check(rows, boundary, (1, 2), (3, 4), sep, 0)

    def test_high_boundary_and_invalid_source(self):
        boundary = (1, 2, 3, 4, 201, 256)
        self.check([[1, 201], [-201, 3], [2, 4]], boundary,
                   (1,), (3,), (201, 256), (1 << 255) | (1 << 200) | 15)
        self.check([[]], (1, 2, 3), (1,), (2,), (3,), 7)
        with self.assertRaises(ValueError):
            audit([[1]], (1, 2, 3), (1,), (2,), (1,), 7, backend="rust")


if __name__ == "__main__":
    unittest.main()
