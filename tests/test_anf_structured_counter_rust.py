"""R-111: bounded structured ANF counter exact results and exact statistics."""
import random
import unittest

from witnora_core.anf_structured_counter import count_common_zeros_structured
from witnora_core.violation_image_anf import ANFCountingBudgetExceeded


class AnfStructuredRustTests(unittest.TestCase):
    def test_seeded_differential(self):
        rng = random.Random(20261119)
        for trial in range(200):
            nvars = rng.randrange(0, 11)
            eqs = []
            for _ in range(rng.randrange(0, 7)):
                terms = set()
                for _ in range(rng.randrange(0, 6)):
                    degree = rng.randrange(0, min(nvars, 5)+1)
                    terms.add(frozenset(rng.sample(range(1, nvars+1), degree)))
                eqs.append(frozenset(terms))
            equations = tuple(eqs)
            options = {"max_states": rng.choice((1, 2, 5, 20, 80, 300))}
            with self.subTest(trial=trial, nvars=nvars):
                try:
                    expected = count_common_zeros_structured(equations, nvars,
                                                             **options)
                except ANFCountingBudgetExceeded:
                    with self.assertRaises(ANFCountingBudgetExceeded):
                        count_common_zeros_structured(equations, nvars,
                                                      backend="rust", **options)
                else:
                    self.assertEqual(count_common_zeros_structured(
                        equations, nvars, backend="rust", **options), expected)

    def test_huge_free_variable_multiplier(self):
        self.assertEqual(count_common_zeros_structured((), 180, backend="rust"),
                         count_common_zeros_structured((), 180))


if __name__ == "__main__":
    unittest.main()
