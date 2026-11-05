"""R-059: all-grammar comparison of opt-in native symbolic implication."""
import os
import random
import unittest

from witnora_core.expression_conjecture_search import expression_pool
from witnora_core.symbolic_implication import (
    KNOWN_BOUNDS, bound_path, bound_path_rust, normalize, normalize_rust,
    derive_equality, derive_equality_rust,
    triage_with_implications, triage_with_implications_rust,
)


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in Rust CI")
class SymbolicImplicationRustTests(unittest.TestCase):
    def test_every_grammar_expression(self):
        for expression in expression_pool():
            with self.subTest(expression=expression.label):
                self.assertEqual(normalize_rust(expression), normalize(expression))

    def test_all_bound_pairs_and_unrecognized_atoms(self):
        symbols = sorted({item for pair in KNOWN_BOUNDS for item in pair} |
                         {"unknown", "0", "1", "2"})
        for smaller in symbols:
            for larger in symbols:
                with self.subTest(smaller=smaller, larger=larger):
                    self.assertEqual(bound_path_rust(smaller, larger),
                                     bound_path(smaller, larger))

    def test_random_grammar_equalities_and_complete_report(self):
        expressions=[x.label for x in expression_pool()]
        rng=random.Random(5902026)
        for case in range(800):
            left,right=rng.choices(expressions,k=2)
            title=f"{left} = {right}"
            with self.subTest(case=case):
                self.assertEqual(derive_equality_rust(title),derive_equality(title))
        self.assertEqual(triage_with_implications_rust(),triage_with_implications())
        with self.assertRaises(ValueError):
            derive_equality_rust("not-in-grammar = n")


if __name__ == "__main__":
    unittest.main()
