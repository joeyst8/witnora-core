"""R-123: native XOR substitution preserves equation metadata."""
import random
import unittest

from witnora_core.xor import XorEquation


class XorSubstituteRustTests(unittest.TestCase):
    def test_seeded_substitutions(self):
        rng = random.Random(20261204)
        for trial in range(500):
            n = rng.choice((3, 30, 200, 350))
            variables = rng.sample(range(1, n+1), rng.randrange(min(n, 11)+1))
            equation = XorEquation(variables, rng.randrange(2),
                                   source="test", pattern_size=3,
                                   safe_use=trial % 2 == 0)
            assignment = {v: bool(rng.randrange(2)) for v in variables
                          if rng.randrange(4) != 0}
            assignment[999] = True
            with self.subTest(trial=trial):
                self.assertEqual(equation.substitute(assignment, backend="rust"),
                                 equation.substitute(assignment))
                self.assertEqual(equation.substitute(assignment, backend="rust").to_dict(),
                                 equation.substitute(assignment).to_dict())


if __name__ == "__main__":
    unittest.main()
