"""R-126: native verification of assignments for XOR systems."""
import random
import unittest

from witnora_core.xor import XorEquation, XorSystem, verify_xor_assignment


class XorVerifyAssignmentRustTests(unittest.TestCase):
    def test_seeded_valid_invalid_and_partial(self):
        rng = random.Random(20261207)
        for trial in range(350):
            nvars = rng.choice((2, 10, 30, 160))
            equations = [XorEquation(rng.sample(
                range(1, nvars+1), rng.randrange(min(8,nvars)+1)),
                rng.randrange(2)) for _ in range(rng.randrange(15))]
            system = XorSystem(equations)
            assignment = {v: bool(rng.randrange(2)) for v in system.variables
                          if rng.randrange(5) != 0}
            with self.subTest(trial=trial):
                self.assertEqual(verify_xor_assignment(system, assignment,
                                                       backend="rust"),
                                 verify_xor_assignment(system, assignment))


if __name__ == "__main__":
    unittest.main()
