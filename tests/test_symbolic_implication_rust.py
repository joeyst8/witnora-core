"""R-059: all-grammar comparison of opt-in native symbolic implication."""
import os
import unittest

from witnora_core.expression_conjecture_search import expression_pool
from witnora_core.symbolic_implication import (
    KNOWN_BOUNDS, bound_path, bound_path_rust, normalize, normalize_rust,
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


if __name__ == "__main__":
    unittest.main()
