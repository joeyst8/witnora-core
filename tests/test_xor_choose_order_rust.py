"""R-137: native Gaussian versus sparse strategy selection differential."""
import random
import unittest

from witnora_core.xor import XorEquation, XorSystem
from witnora_core.xor_drat import _choose_order, XOR_ELIM_SPARSE_MIN_FILL, XOR_ELIM_GAUSSIAN


class XorChooseOrderRustTests(unittest.TestCase):
    def test_both_strategies(self):
        rng = random.Random(137)
        for trial in range(65):
            equations = [XorEquation(rng.sample(range(1, 9), rng.randrange(0, 6)),
                                     rng.randrange(2)) for _ in range(rng.randrange(1, 6))]
            solution = {"status": rng.choice(["SAT", "UNSAT"]),
                        "elimination_trace": [
                            {"type": "pivot", "pivot": rng.randrange(1, 9),
                             "variables": rng.sample(range(1, 9), rng.randrange(0, 6))}
                            for _ in range(rng.randrange(0, 5))]}
            system = XorSystem(equations)
            for strategy in [XOR_ELIM_GAUSSIAN, XOR_ELIM_SPARSE_MIN_FILL]:
                with self.subTest(trial=trial, strategy=strategy):
                    args = (solution, system, equations)
                    self.assertEqual(_choose_order(*args, xor_elim_order=strategy,
                                                   backend="rust"),
                                     _choose_order(*args, xor_elim_order=strategy))


if __name__ == "__main__":
    unittest.main()
