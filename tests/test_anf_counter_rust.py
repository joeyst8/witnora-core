"""R-108: bounded exact symbolic Shannon counts and exhaustion semantics."""
import random
import unittest

from witnora_core.violation_image_anf import (
    ANFCountingBudgetExceeded, count_common_zeros,
)


class AnfCounterRustTests(unittest.TestCase):
    def test_random_equations_and_budgets(self):
        rng = random.Random(20261115)
        for trial in range(150):
            nvars = rng.randrange(0, 9)
            eqs = []
            for _ in range(rng.randrange(0, 6)):
                monomials = set()
                for _ in range(rng.randrange(0, 6)):
                    degree = rng.randrange(0, min(nvars, 4) + 1)
                    monomials.add(frozenset(rng.sample(range(1, nvars+1), degree)))
                eqs.append(frozenset(monomials))
            equations = tuple(eqs)
            max_states = rng.choice((1, 2, 5, 20, 200, 1000))
            with self.subTest(trial=trial, nvars=nvars, max_states=max_states):
                try:
                    reference = count_common_zeros(equations, nvars,
                                                    max_states=max_states)
                except ANFCountingBudgetExceeded:
                    with self.assertRaises(ANFCountingBudgetExceeded):
                        count_common_zeros(equations, nvars,
                                           max_states=max_states, backend="rust")
                else:
                    self.assertEqual(count_common_zeros(
                        equations, nvars, max_states=max_states, backend="rust"),
                        reference)

    def test_arbitrary_width_and_invalid(self):
        expected = count_common_zeros((), 150)
        self.assertEqual(count_common_zeros((), 150, backend="rust"), expected)
        with self.assertRaises(ValueError):
            count_common_zeros((frozenset({frozenset({3})}),), 2,
                               backend="rust")


if __name__ == "__main__":
    unittest.main()
