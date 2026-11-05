"""R-149/R-150: differential row-resolution proof candidate and cap behavior."""
import random
import time
import unittest

from witnora_core.xor_drat import (
    _derive_row_encoding_from_parent_rows,
    _xor_encoding_clauses,
)


class XorRowDerivationRustTests(unittest.TestCase):
    def test_seeded_parent_row_derivation(self):
        rng = random.Random(149150)
        for trial in range(180):
            universe = list(range(1, 8))
            left_variables = frozenset(rng.sample(universe, rng.randrange(0, 5)))
            right_variables = frozenset(rng.sample(universe, rng.randrange(0, 5)))
            left_rhs, right_rhs = rng.randrange(2), rng.randrange(2)
            left = _xor_encoding_clauses(left_variables, left_rhs)
            right = _xor_encoding_clauses(right_variables, right_rhs)
            expected = _xor_encoding_clauses(left_variables ^ right_variables,
                                             left_rhs ^ right_rhs)
            active = set(left | right)
            for clause in expected:
                if rng.randrange(4) == 0:
                    active.add(clause)
            original_lines = ["seed 0"] if trial % 7 == 0 else []
            emitted, proof_bytes = rng.randrange(0, 4), rng.randrange(0, 12)
            max_width = rng.randrange(0, 6)
            options = dict(
                left_encoding=left, right_encoding=right,
                left_value=(left_variables, left_rhs),
                right_value=(right_variables, right_rhs),
                expected_encoding=expected,
                emitted=emitted, proof_bytes=proof_bytes, max_width=max_width,
                max_proof_clauses=rng.randrange(0, 120),
                max_proof_bytes=rng.randrange(0, 2000), timeout_seconds=None)
            left_lines, right_lines = list(original_lines), list(original_lines)
            rust_active, python_active = set(active), set(active)
            with self.subTest(trial=trial):
                rust = _derive_row_encoding_from_parent_rows(
                    **options, lines=left_lines, active=rust_active,
                    started=time.perf_counter(), backend="rust")
                python = _derive_row_encoding_from_parent_rows(
                    **options, lines=right_lines, active=python_active,
                    started=time.perf_counter())
                self.assertEqual((rust, left_lines, rust_active),
                                 (python, right_lines, python_active))


if __name__ == "__main__":
    unittest.main()
