"""R-061: symbolic identity normalizer/catalog differential checks."""
import os
import random
import unittest

from witnora_core.expression_conjecture_search import expression_pool
from witnora_core.conjecture_triage import (
    normalize_expression, normalize_expression_rust,
    identity_key, identity_key_rust,
    known_identity_keys, known_identity_keys_rust,
)


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in Rust CI")
class ConjectureTriageRustTests(unittest.TestCase):
    def test_complete_current_grammar(self):
        expressions = [x.label for x in expression_pool()]
        for expression in expressions:
            with self.subTest(expression=expression):
                self.assertEqual(normalize_expression_rust(expression),
                                 normalize_expression(expression))
        rng = random.Random(6102026)
        for _ in range(800):
            left, right = rng.choices(expressions, k=2)
            title = f"{left} = {right}"
            self.assertEqual(identity_key_rust(title), identity_key(title))

    def test_known_catalog_and_malformed_controls(self):
        self.assertEqual(known_identity_keys_rust(), known_identity_keys())
        for bad in ("min(a,b,c)", "max(a,b,c)"):
            with self.assertRaises(ValueError):
                normalize_expression_rust(bad)
            with self.assertRaises(ValueError):
                normalize_expression(bad)
        with self.assertRaises(ValueError):
            identity_key_rust("missing equals")


if __name__ == "__main__":
    unittest.main()
