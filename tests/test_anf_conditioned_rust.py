"""R-112: native composed ANF conditioned counters and exact statistics."""
import random
import unittest

from witnora_core.anf_separator_conditioning import count_common_zeros_conditioned
from witnora_core.violation_image_anf import ANFCountingBudgetExceeded


class AnfConditionedRustTests(unittest.TestCase):
    def test_seeded_differential(self):
        rng = random.Random(20261120)
        for trial in range(130):
            nvars = rng.randrange(1, 10)
            equations = []
            for _ in range(rng.randrange(0, 7)):
                terms = set()
                for _ in range(rng.randrange(0, 6)):
                    degree = rng.randrange(0, min(nvars, 4)+1)
                    terms.add(frozenset(rng.sample(range(1, nvars+1), degree)))
                equations.append(frozenset(terms))
            options = {"max_states": rng.choice((1, 3, 20, 200, 1000)),
                       "max_separator_size": rng.choice((0, 1, 2)),
                       "max_candidate_checks": rng.choice((1, 10, 60))}
            with self.subTest(trial=trial, nvars=nvars):
                try:
                    expected = count_common_zeros_conditioned(
                        tuple(equations), nvars, **options)
                except ANFCountingBudgetExceeded:
                    with self.assertRaises(ANFCountingBudgetExceeded):
                        count_common_zeros_conditioned(
                            tuple(equations), nvars, backend="rust", **options)
                else:
                    self.assertEqual(count_common_zeros_conditioned(
                        tuple(equations), nvars, backend="rust", **options), expected)


if __name__ == "__main__":
    unittest.main()
