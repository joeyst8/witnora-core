"""R-121: differential XOR variable toggle-and-sort normalization."""
import random
import unittest

from witnora_core.xor import _normalize_xor_variables


class XorNormalizeRustTests(unittest.TestCase):
    def test_constants_and_repeated_variables(self):
        for sequence in ((), (1,), (1, 1), (3, 1, 3, 2, 1, 7),
                         (129, 300, 129), ("3", "3", "8")):
            with self.subTest(sequence=sequence):
                self.assertEqual(_normalize_xor_variables(sequence, backend="rust"),
                                 _normalize_xor_variables(sequence))

    def test_seeded_parity_toggle(self):
        rng = random.Random(20261202)
        for trial in range(400):
            values = [rng.randint(1, rng.choice((6, 64, 512)))
                      for _ in range(rng.randrange(60))]
            with self.subTest(trial=trial):
                self.assertEqual(_normalize_xor_variables(values, backend="rust"),
                                 _normalize_xor_variables(values))

    def test_bad_variable(self):
        for backend in ("python", "rust"):
            with self.subTest(backend=backend):
                with self.assertRaisesRegex(ValueError, "must be positive"):
                    _normalize_xor_variables((1, 0), backend=backend)


if __name__ == "__main__":
    unittest.main()
