"""Independent regression tests for reproducible GF(2) benchmark baselines."""
from itertools import combinations, product
import random
import unittest

from scripts.benchmark_cycle_discovery import (
    gaussian_gf2_unsat, make_case, parity_union_find_unsat,
)
from witnora_core.cycle_discovery import discover_odd_xor_cycle


def exhaustive_xor_unsat(edges, n):
    return not any(
        all((values[u-1] ^ values[v-1]) == bit for u, v, bit in edges)
        for values in product((0, 1), repeat=n)
    )


class CycleBenchmarkTest(unittest.TestCase):
    def test_independent_baselines_match_exhaustive_truth(self):
        rng = random.Random(63063)
        for n in range(3, 8):
            for _ in range(50):
                edges = [(u, v, rng.randrange(2))
                         for u, v in combinations(range(1, n+1), 2)
                         if rng.random() < 0.5]
                expected = exhaustive_xor_unsat(edges, n)
                self.assertEqual(parity_union_find_unsat(edges), expected)
                self.assertEqual(gaussian_gf2_unsat(edges), expected)

    def test_benchmark_cases_expose_non_xor_unsat_gap(self):
        for n in (4, 8, 24):
            for kind in ("consistent_cycle", "contradictory_cycle",
                         "consistent_dense", "contradictory_dense", "non_xor_unsat"):
                formula, edges, truth = make_case(n, kind, 63063)
                xor_unsat = kind.startswith("contradictory")
                self.assertEqual(parity_union_find_unsat(edges), xor_unsat)
                self.assertEqual(gaussian_gf2_unsat(edges), xor_unsat)
                self.assertEqual(discover_odd_xor_cycle(formula) is not None, xor_unsat)
                self.assertEqual(truth, xor_unsat or kind == "non_xor_unsat")


if __name__ == "__main__":
    unittest.main()
