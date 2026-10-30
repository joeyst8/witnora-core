"""Expression semantics and finite claim boundary tests."""
import unittest

from witnora_core.expression_conjecture_search import Expr, run_expression_search


class ExpressionSearchTests(unittest.TestCase):
    def test_arithmetic_semantics(self):
        values = {"n": 5, "alpha": 3, "tau": 2, "m": 4}
        self.assertEqual(Expr("+", "alpha", "tau").evaluate(values), 5)
        self.assertEqual(Expr("-", "n", "tau").evaluate(values), 3)
        self.assertEqual(Expr("min", "n", "alpha").evaluate(values), 3)
        self.assertEqual(Expr("*", "alpha", "2").evaluate(values), 6)

    def test_recovered_known_identity_is_unproved(self):
        result = run_expression_search(holdout_per_size=25)
        survivors = set(result["holdout_survivors"])
        self.assertTrue(any("alpha" in s and "tau" in s and "n" in s
                            for s in survivors))
        self.assertEqual(result["known_identity_review"], "NOT_PERFORMED")
        self.assertFalse(result["theorem_proven"])


if __name__ == "__main__":
    unittest.main()
