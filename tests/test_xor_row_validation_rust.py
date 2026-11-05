"""R-145/R-146: differential parent lookup and exact XOR row validation."""
import random
import unittest

from witnora_core.xor_drat import _validate_row_operation_values


class XorRowValidationRustTests(unittest.TestCase):
    def test_random_rows_and_claims(self):
        rng = random.Random(145146)
        for trial in range(420):
            rows = {
                f"row_{i}": (frozenset(rng.sample(range(1, 14), rng.randrange(0, 9))),
                              rng.randrange(2))
                for i in range(rng.randrange(0, 13))
            }
            names = list(rows)
            left = rng.choice(names + ["missing_a"])
            right = rng.choice(names + ["missing_b"])
            vars_ = frozenset(rng.sample(range(1, 14), rng.randrange(0, 9)))
            rhs = rng.randrange(4)
            with self.subTest(trial=trial):
                self.assertEqual(
                    _validate_row_operation_values(rows, left, right, vars_, rhs, backend="rust"),
                    _validate_row_operation_values(rows, left, right, vars_, rhs))

    def test_known_exact_and_rejections(self):
        rows = {"A": (frozenset({1, 2}), 1), "B": (frozenset({2, 3}), 1)}
        for left, right, variables, rhs, expected in [
            ("A", "B", frozenset({1, 3}), 0, None),
            ("A", "missing", frozenset({1, 3}), 0, "ROW_OPERATION_PARENT_MISSING"),
            ("A", "B", frozenset({1, 2, 3}), 0, "ROW_OPERATION_VALUE_MISMATCH"),
            ("A", "B", frozenset({1, 3}), 1, "ROW_OPERATION_VALUE_MISMATCH"),
        ]:
            self.assertEqual(_validate_row_operation_values(rows, left, right, variables,
                              rhs, backend="rust"), expected)


if __name__ == "__main__":
    unittest.main()
