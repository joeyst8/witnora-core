"""R-125: exact differential XOR Gaussian-elimination certificates/traces."""
import random
import unittest

from witnora_core.xor import XorEquation, XorSystem, solve_xor_system_gaussian


class XorGaussianRustTests(unittest.TestCase):
    def test_adversarial_cases(self):
        systems = ((), (XorEquation([], 1),),
                   (XorEquation([1], 0), XorEquation([1], 1)),
                   (XorEquation([1, 2], 1), XorEquation([2, 3], 0)),
                   (XorEquation([1], 1), XorEquation([1], 1)))
        for equations in systems:
            with self.subTest(equations=equations):
                system = XorSystem(equations)
                self.assertEqual(solve_xor_system_gaussian(system, backend="rust"),
                                 solve_xor_system_gaussian(system))

    def test_seeded_full_trace(self):
        rng = random.Random(20261206)
        for trial in range(350):
            nvars = rng.choice((2, 8, 23, 130))
            equations = [XorEquation(rng.sample(
                range(1, nvars+1), rng.randrange(min(nvars, 10)+1)),
                rng.randrange(2)) for _ in range(rng.randrange(13))]
            system = XorSystem(equations)
            with self.subTest(trial=trial):
                observed = solve_xor_system_gaussian(system, backend="rust")
                self.assertEqual(observed, solve_xor_system_gaussian(system))


if __name__ == "__main__":
    unittest.main()
