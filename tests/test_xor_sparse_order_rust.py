"""R-134: native sparse elimination order wrapper and summary parity."""
import random
import unittest

from witnora_core.xor import XorEquation
from witnora_core.xor_drat import _sparse_xor_elimination_order


class XorSparseOrderRustTests(unittest.TestCase):
    def test_seeded_orders(self):
        rng = random.Random(20261215)
        for trial in range(100):
            nvars = rng.randrange(2, 11)
            equations = tuple(XorEquation(rng.sample(range(1,nvars+1),
                                           rng.randrange(min(nvars,5)+1)),
                                          rng.randrange(2))
                              for _ in range(rng.randrange(1, 7)))
            with self.subTest(trial=trial):
                self.assertEqual(_sparse_xor_elimination_order(
                    equations, backend="rust"),
                    _sparse_xor_elimination_order(equations))


if __name__ == "__main__":
    unittest.main()
