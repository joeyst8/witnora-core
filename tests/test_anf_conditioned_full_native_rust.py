"""R-119: single-call native separator-conditioned exact ANF counting."""
import random
import unittest

from witnora_core.anf_separator_conditioning import count_common_zeros_conditioned
from witnora_core.violation_image_anf import ANFCountingBudgetExceeded


class FullAnfConditionedRustTests(unittest.TestCase):
    def test_seeded_results_and_accounting(self):
        rng = random.Random(20261130)
        for trial in range(160):
            nvars = rng.randrange(1, 12)
            equations = []
            for _ in range(rng.randrange(0, 8)):
                terms = set()
                for _ in range(rng.randrange(0, 7)):
                    degree = rng.randrange(0, min(nvars, 5)+1)
                    terms.add(frozenset(rng.sample(range(1, nvars+1), degree)))
                equations.append(frozenset(terms))
            opts = {"max_states": rng.choice((1, 4, 20, 200, 1000)),
                    "max_separator_size": rng.choice((0, 1, 2)),
                    "max_candidate_checks": rng.choice((1, 10, 100))}
            with self.subTest(trial=trial):
                try:
                    expected = count_common_zeros_conditioned(tuple(equations),
                                                              nvars, **opts)
                except ANFCountingBudgetExceeded:
                    with self.assertRaises(ANFCountingBudgetExceeded):
                        count_common_zeros_conditioned(tuple(equations), nvars,
                                                       backend="rust", **opts)
                else:
                    self.assertEqual(count_common_zeros_conditioned(
                        tuple(equations), nvars, backend="rust", **opts), expected)

    def test_wide_free_vars(self):
        self.assertEqual(count_common_zeros_conditioned((), 180, backend="rust"),
                         count_common_zeros_conditioned((), 180))


if __name__ == "__main__":
    unittest.main()
