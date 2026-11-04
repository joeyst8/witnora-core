"""R-109: native arbitrary-width scope connectivity and bounded separators."""
import random
import unittest

from witnora_core.anf_separator_conditioning import (
    residual_component_sizes, find_bounded_separator,
)


class AnfSeparatorRustTests(unittest.TestCase):
    def test_component_sizes_differential(self):
        rng = random.Random(20261116)
        for trial in range(340):
            n = rng.randrange(0, 145)
            scopes = tuple(sum(1 << v for v in rng.sample(
                range(n), rng.randrange(0, min(n, 8)+1)))
                for _ in range(rng.randrange(0, 10)))
            removed = sum(1 << v for v in rng.sample(
                range(n), rng.randrange(0, min(n, 8)+1)))
            with self.subTest(trial=trial, n=n):
                self.assertEqual(residual_component_sizes(scopes, removed,
                                                          backend="rust"),
                                 residual_component_sizes(scopes, removed))

    def test_separator_search_differential(self):
        rng = random.Random(20261117)
        for trial in range(85):
            n = rng.randrange(1, 13)
            equations = []
            for _ in range(rng.randrange(0, 8)):
                monomials = set()
                for _ in range(rng.randrange(0, 5)):
                    degree = rng.randrange(0, min(n, 4)+1)
                    monomials.add(frozenset(rng.sample(range(1, n+1), degree)))
                equations.append(frozenset(monomials))
            eqs = tuple(equations)
            options = {"max_separator_size": rng.choice((0, 1, 2)),
                       "max_candidate_checks": rng.choice((1, 8, 40, 200))}
            with self.subTest(trial=trial, n=n):
                self.assertEqual(find_bounded_separator(eqs, n,
                                                        backend="rust", **options),
                                 find_bounded_separator(eqs, n, **options))


if __name__ == "__main__":
    unittest.main()
