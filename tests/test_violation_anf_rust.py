"""R-107: compare Boolean-quotient GF(2) polynomial algebra exactly."""
import random
import unittest

from witnora_core.violation_image_anf import (
    xor_polynomials, multiply_polynomials, substitute, canonical_equations,
)


class AnfPolynomialRustTests(unittest.TestCase):
    def test_seeded_polynomial_algebra(self):
        rng = random.Random(20261114)

        def poly():
            terms = set()
            for _ in range(rng.randrange(0, 12)):
                term = frozenset(rng.sample(range(1, 13), rng.randrange(0, 5)))
                terms.add(term)
            return frozenset(terms)

        for trial in range(270):
            a, b = poly(), poly()
            variable = rng.randrange(1, 13)
            with self.subTest(trial=trial):
                self.assertEqual(xor_polynomials(a, b, backend="rust"),
                                 xor_polynomials(a, b))
                self.assertEqual(multiply_polynomials(a, b, backend="rust"),
                                 multiply_polynomials(a, b))
                for bit in (False, True):
                    self.assertEqual(substitute(a, variable, bit, backend="rust"),
                                     substitute(a, variable, bit))
                equations = (a, b, a, frozenset(), poly())
                self.assertEqual(canonical_equations(equations, backend="rust"),
                                 canonical_equations(equations))


if __name__ == "__main__":
    unittest.main()
