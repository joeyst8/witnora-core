"""R-127: full bounded XOR CNF encoding under native parity enumeration."""
import random
import unittest

from witnora_core.xor import canonical_xor_cnf_clauses


class XorCanonicalCnfRustTests(unittest.TestCase):
    def test_small_exhaustive_widths_and_repetition(self):
        for n in range(9):
            for parity in (0, 1):
                variables = list(range(1, n+1))
                with self.subTest(n=n, parity=parity):
                    self.assertEqual(canonical_xor_cnf_clauses(
                        variables, parity, backend="rust"),
                        canonical_xor_cnf_clauses(variables, parity))
        self.assertEqual(canonical_xor_cnf_clauses([1, 1, 2], 1, backend="rust"),
                         canonical_xor_cnf_clauses([1, 1, 2], 1))

    def test_seeded_supports(self):
        rng = random.Random(20261208)
        for trial in range(240):
            size = rng.randrange(9)
            variables = rng.sample(range(1, 230), size)
            parity = rng.randrange(2)
            with self.subTest(trial=trial):
                self.assertEqual(canonical_xor_cnf_clauses(
                    variables, parity, backend="rust"),
                    canonical_xor_cnf_clauses(variables, parity))

    def test_fail_closed_cap(self):
        with self.assertRaisesRegex(ValueError, "width limit"):
            canonical_xor_cnf_clauses(range(1, 18), 0, backend="rust")


if __name__ == "__main__":
    unittest.main()
