"""R-083 budgeted exact Shannon/Walsh native differential oracle."""
import random
import unittest

from witnora_core.crc_shannon_oracle import query_walsh_coefficients
from tests.test_crc_shannon_oracle import violations


class ShannonRustTests(unittest.TestCase):
    def setUp(self):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            self.skipTest("native Rust wheel not installed")

    def test_160_seeded_source_recursions(self):
        rng = random.Random(83083)
        for trial in range(160):
            n = rng.randrange(1, 9)
            boundary = tuple(range(1, n + 1))
            source = tuple(tuple(rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                             for _ in range(rng.randrange(1, 5)))
                           for _ in range(rng.randrange(0, 16)))
            mode_count = rng.randrange(1, 1 << min(n, 5))
            modes = tuple(rng.randrange(1 << n) for _ in range(mode_count))
            normalized = violations(source)
            budget = rng.choice((1, 3, 10, 40, 100_000))
            with self.subTest(trial=trial):
                self.assertEqual(query_walsh_coefficients(normalized, boundary,
                    modes, max_states=budget, backend="rust"),
                    query_walsh_coefficients(normalized, boundary, modes,
                                             max_states=budget))

    def test_empty_contradiction_and_256_bit_boundary(self):
        cases = [
            ((), (1, 2, 3), (0, 1, 7), 50),
            (None, (1, 2, 3), (0, 7), 50),
            (((0, 0),), (1,), (0, 1), 50),
            (((1, 0),), (1, 256), (0, 1, 1 << 255), 50),
            (((1, 0), (1 << 255, 0)), (1, 256), (0, 1, 1 << 255), 50),
        ]
        for normalized, boundary, modes, budget in cases:
            self.assertEqual(query_walsh_coefficients(normalized, boundary,
                modes, max_states=budget, backend="rust"),
                query_walsh_coefficients(normalized, boundary, modes,
                                         max_states=budget))


if __name__ == "__main__":
    unittest.main()
