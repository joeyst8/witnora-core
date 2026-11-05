"""R-120: arbitrary-width ANF scope masks via native Rust."""
import random
import unittest

from witnora_core.anf_separator_conditioning import polynomial_scopes


class AnfScopesRustTests(unittest.TestCase):
    def test_large_indices_and_constants(self):
        equations = (frozenset({frozenset({1, 130, 257})}),
                     frozenset({frozenset()}), frozenset())
        self.assertEqual(polynomial_scopes(equations, backend="rust"),
                         polynomial_scopes(equations))

    def test_seeded_masks(self):
        rng = random.Random(20261201)
        for trial in range(350):
            nvars = rng.choice((2, 9, 63, 128, 180, 300))
            equations = []
            for _ in range(rng.randrange(0, 7)):
                terms = frozenset(frozenset(rng.sample(
                    range(1, nvars+1), rng.randrange(0, min(nvars, 4)+1)))
                    for _ in range(rng.randrange(0, 5)))
                equations.append(terms)
            with self.subTest(trial=trial):
                self.assertEqual(polynomial_scopes(tuple(equations), backend="rust"),
                                 polynomial_scopes(tuple(equations)))

    def test_bad_id(self):
        equations = (frozenset({frozenset({0})}),)
        for backend in ("python", "rust"):
            with self.subTest(backend=backend):
                with self.assertRaises(ValueError):
                    polynomial_scopes(equations, backend=backend)


if __name__ == "__main__":
    unittest.main()
