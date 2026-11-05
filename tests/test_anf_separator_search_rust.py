"""R-110: complete native bounded separator choice with exact budget accounting."""
import random
import unittest

from witnora_core.anf_separator_conditioning import find_bounded_separator


class AnfSeparatorSearchRustTests(unittest.TestCase):
    def test_seeded_searches(self):
        rng = random.Random(20261118)
        for trial in range(135):
            n = rng.randrange(0, 13) if trial < 125 else rng.randrange(33, 48)
            equations = []
            for _ in range(rng.randrange(0, 10)):
                terms = set()
                for _ in range(rng.randrange(0, 5)):
                    degree = rng.randrange(0, min(n, 5)+1)
                    terms.add(frozenset(rng.sample(range(1, n+1), degree)))
                equations.append(frozenset(terms))
            eqs = tuple(equations)
            options = {"max_separator_size": rng.choice((0, 1, 2, 3)),
                       "max_candidate_checks": rng.choice((1, 2, 10, 60, 200))}
            with self.subTest(trial=trial, n=n):
                self.assertEqual(find_bounded_separator(eqs, n,
                                                        backend="rust", **options),
                                 find_bounded_separator(eqs, n, **options))

    def test_invalid_limits(self):
        for backend in ("python", "rust"):
            with self.assertRaises(ValueError):
                find_bounded_separator((), 3, max_candidate_checks=0,
                                       backend=backend)


if __name__ == "__main__":
    unittest.main()
