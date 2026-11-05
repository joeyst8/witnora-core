"""R-114: GF(2) polynomial evaluation through the optional native backend."""
import random
import unittest

from witnora_core.violation_image_anf import (
    ONE, ZERO, evaluate_polynomial, variable, xor_polynomials,
)


class AnfEvaluateRustTests(unittest.TestCase):
    def test_constants_and_high_bits(self):
        for assignment in (0, 1, 1 << 128, 1 << 129, (1 << 256) - 1):
            for poly in (ONE, ZERO, variable(130), variable(257),
                         xor_polynomials(variable(1), variable(130))):
                with self.subTest(assignment=assignment, poly=poly):
                    self.assertEqual(evaluate_polynomial(poly, assignment, backend="rust"),
                                     evaluate_polynomial(poly, assignment))

    def test_seeded_polynomials_and_assignments(self):
        rng = random.Random(20261125)
        variables = (1, 2, 4, 11, 63, 64, 127, 128, 130, 191, 257)
        for index in range(350):
            poly = frozenset(frozenset(rng.sample(variables, rng.randrange(5)))
                             for _ in range(rng.randrange(18)))
            assignment = rng.getrandbits(270)
            with self.subTest(index=index):
                self.assertEqual(evaluate_polynomial(poly, assignment, backend="rust"),
                                 evaluate_polynomial(poly, assignment))

    def test_input_validation(self):
        for backend in ("python", "rust"):
            with self.subTest(backend=backend):
                with self.assertRaises(ValueError):
                    evaluate_polynomial(variable(1), -1, backend=backend)
        with self.assertRaises(ValueError):
            evaluate_polynomial(variable(1), 0, backend="unknown")


if __name__ == "__main__":
    unittest.main()
