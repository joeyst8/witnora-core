"""R-133: exact native sparse/min-fill row-operation schedule and trace."""
import random
import unittest

from witnora_core.xor import XorEquation
from witnora_core.xor_drat import _sparse_xor_elimination_schedule


class XorSparseScheduleRustTests(unittest.TestCase):
    def test_seeded_complete_schedule(self):
        rng = random.Random(20261214)
        for trial in range(120):
            nvars = rng.randrange(2, 11)
            equations = tuple(XorEquation(rng.sample(range(1,nvars+1),
                                           rng.randrange(min(nvars,5)+1)),
                                          rng.randrange(2))
                              for _ in range(rng.randrange(1, 8)))
            with self.subTest(trial=trial):
                self.assertEqual(_sparse_xor_elimination_schedule(
                    equations, backend="rust"),
                    _sparse_xor_elimination_schedule(equations))

    def test_initial_contradiction(self):
        equations = (XorEquation([],1),XorEquation([1],1))
        self.assertEqual(_sparse_xor_elimination_schedule(
            equations, backend="rust"), _sparse_xor_elimination_schedule(equations))


if __name__ == "__main__":
    unittest.main()
