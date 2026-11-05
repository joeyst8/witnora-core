"""R-138: exact native XOR encoding through DRAT bridge helper."""
import random
import unittest

from witnora_core.xor_drat import _xor_encoding_clauses


class XorDratEncodingRustTests(unittest.TestCase):
    def test_seeded_supports(self):
        rng = random.Random(138)
        for trial in range(180):
            variables = rng.choices(range(1, 13), k=rng.randrange(0, 8))
            rhs = rng.randrange(0, 4)
            with self.subTest(trial=trial):
                self.assertEqual(_xor_encoding_clauses(variables, rhs,
                                                       backend="rust"),
                                 _xor_encoding_clauses(variables, rhs))


if __name__ == "__main__":
    unittest.main()
