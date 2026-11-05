"""R-124: one Rust call for a whole XOR system's substitution."""
import random
import unittest

from witnora_core.xor import XorEquation, XorSystem


class XorSystemSubstituteRustTests(unittest.TestCase):
    def test_seeded_systems(self):
        rng = random.Random(20261205)
        for trial in range(300):
            n = rng.choice((3, 14, 80, 200))
            equations = [XorEquation(rng.sample(
                range(1, n+1), rng.randrange(min(n, 10)+1)),
                rng.randrange(2), source="test", safe_use=trial%2==0)
                for _ in range(rng.randrange(10))]
            system = XorSystem(equations, diagnostics=[{"trial":trial}])
            assignment = {v: bool(rng.randrange(2)) for v in system.variables
                          if rng.randrange(3) != 0}
            with self.subTest(trial=trial):
                expected = system.substitute(assignment)
                observed = system.substitute(assignment, backend="rust")
                self.assertEqual(observed, expected)
                self.assertEqual(observed.to_dict(), expected.to_dict())


if __name__ == "__main__":
    unittest.main()
