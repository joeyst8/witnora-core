"""R-075 exact native source-bound sufficient independence comparisons."""
import random
import unittest

from witnora_core.crc_structural_independence import (
    audit_structural_source_independence as audit,
)


class StructuralIndependenceRustTests(unittest.TestCase):
    def setUp(self):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            self.skipTest("native Rust wheel not installed")

    def check(self, rows, boundary, left, right, witness):
        expected = audit(rows, boundary, left, right, witness)
        native = audit(rows, boundary, left, right, witness, backend="rust")
        self.assertEqual(native, expected)

    def test_400_seeded_compatibility_and_invalid_witnesses(self):
        rng = random.Random(75075)
        for trial in range(400):
            n = rng.randrange(4, 15)
            boundary = tuple(range(1, n + 1))
            rows = []
            for _ in range(rng.randrange(22)):
                chosen = rng.sample(boundary, rng.randrange(1, 5))
                rows.append([v if rng.randrange(2) else -v for v in chosen])
            left, right = (1, 2), (3, 4)
            witness = rng.getrandbits(n)
            with self.subTest(trial=trial):
                self.check(rows, boundary, left, right, witness)
        self.check([[]], (1, 2), (1,), (2,), 3)
        self.check([[1, -1], [2]], (1, 2), (1,), (2,), 2)
        self.check([[1, 2], [3, 4]], (1, 2, 3, 4), (1, 2), (3, 4), 15)
        self.check([[1], [2], [1, 2]], (1, 2), (1,), (2,), 3)

    def test_high_bit_and_contract_rejections(self):
        boundary = (1, 2, 201, 256)
        self.check([[201, 256], [1, 2]], boundary, (1, 2), (201, 256),
                   (1 << 200) | (1 << 255) | 3)
        with self.assertRaises(ValueError):
            audit([[3]], (1, 2), (1,), (2,), 3, backend="rust")
        with self.assertRaises(ValueError):
            audit([[1]], (1, 2), (1,), (2,), 1 << 10, backend="rust")
        with self.assertRaises(ValueError):
            audit([[1]], (1, 2), (1,), (1,), 1, backend="rust")


if __name__ == "__main__":
    unittest.main()
