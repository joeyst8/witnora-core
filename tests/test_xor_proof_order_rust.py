"""R-135: seeded trace-pivot ordering differential (not a proof checker)."""
import random
import unittest

from witnora_core.xor import XorEquation, XorSystem
from witnora_core.xor_drat import _proof_order


class XorProofOrderRustTests(unittest.TestCase):
    def test_seeded_pivot_orders(self):
        rng = random.Random(135)
        for trial in range(160):
            system = XorSystem(XorEquation(rng.sample(range(1, 13),
                        rng.randrange(0, 7)), rng.randrange(2))
                               for _ in range(rng.randrange(1, 7)))
            pivots = [rng.randrange(1, 13) for _ in range(rng.randrange(0, 12))]
            trace = [{"type": "pivot", "pivot": v} for v in pivots]
            trace.insert(0, {"type": "input_row", "variables": [1, 3], "rhs": 1})
            sol = {"elimination_trace": trace}
            with self.subTest(trial=trial):
                self.assertEqual(_proof_order(sol, system, backend="rust"),
                                 _proof_order(sol, system))


if __name__ == "__main__":
    unittest.main()
