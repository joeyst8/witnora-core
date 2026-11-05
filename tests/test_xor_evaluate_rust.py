"""R-122: native evaluation of partially assigned XOR equations."""
import random
import unittest

from witnora_core.xor import XorEquation


class XorEvaluateRustTests(unittest.TestCase):
    def test_seeded_partial_assignments(self):
        rng = random.Random(20261203)
        for trial in range(500):
            n = rng.choice((3, 30, 200, 350))
            variables = rng.sample(range(1, n+1), rng.randrange(min(n, 11)+1))
            equation = XorEquation(variables, rng.randrange(2))
            assignment = {v: bool(rng.randrange(2)) for v in variables
                          if rng.randrange(4) != 0}
            assignment[999] = True
            with self.subTest(trial=trial):
                self.assertEqual(equation.evaluate(assignment, backend="rust"),
                                 equation.evaluate(assignment))


if __name__ == "__main__":
    unittest.main()
