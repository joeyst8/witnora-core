"""R-136: native Gaussian order metadata exactly matches Python reference."""
import random
import unittest

from witnora_core.xor import XorEquation, XorSystem
from witnora_core.xor_drat import _gaussian_order_stats


class XorGaussianStatsRustTests(unittest.TestCase):
    def test_seeded_widths_and_contradiction(self):
        rng = random.Random(136)
        for trial in range(130):
            equations = [XorEquation(rng.sample(range(1, 16),
                             rng.randrange(0, 8)), rng.randrange(2))
                         for _ in range(rng.randrange(0, 7))]
            trace = []
            for _ in range(rng.randrange(0, 13)):
                kind = rng.choice(["pivot", "xor_eliminate", "input_row", "contradiction"])
                event = {"type": kind}
                if kind == "pivot":
                    event["pivot"] = rng.randrange(1, 16)
                for key in ("variables", "before", "after"):
                    if rng.choice([True, False]):
                        event[key] = rng.sample(range(1, 16), rng.randrange(0, 10))
                trace.append(event)
            sol = {"elimination_trace": trace,
                   "status": rng.choice(["SAT", "UNSAT"])}
            with self.subTest(trial=trial):
                self.assertEqual(_gaussian_order_stats(sol, XorSystem(equations),
                                equations, backend="rust"),
                                 _gaussian_order_stats(sol, XorSystem(equations), equations))


if __name__ == "__main__":
    unittest.main()
