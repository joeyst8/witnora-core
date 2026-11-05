"""R-088 expression grammar and holdout native/Python source differential."""
import random
import unittest

from witnora_core.expression_conjecture_search import (
    ATOMS, OPS, Expr, run_expression_search,
)


class ExpressionRustTests(unittest.TestCase):
    def setUp(self):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            self.skipTest("native Rust wheel not installed")

    def test_180_seeded_expression_values(self):
        rng = random.Random(88088)
        for trial in range(180):
            values = {name: rng.randrange(0, 21) for name in ATOMS if name not in ("0", "1", "2")}
            op = rng.choice(("atom",) + OPS)
            a, b = rng.choice(ATOMS), rng.choice(ATOMS)
            expr = Expr(op, a, b)
            with self.subTest(trial=trial):
                self.assertEqual(expr.evaluate(values, backend="rust"), expr.evaluate(values))

    def test_complete_holdout_reports(self):
        for count, limit in ((5, 60), (12, 150), (25, 1500)):
            with self.subTest(count=count, limit=limit):
                self.assertEqual(run_expression_search(holdout_per_size=count,
                                                       max_candidates=limit,
                                                       backend="rust"),
                                 run_expression_search(holdout_per_size=count,
                                                       max_candidates=limit))


if __name__ == "__main__":
    unittest.main()
