"""R-115: a single native call for each signed clause violation indicator."""
import random
import unittest

from witnora_core.violation_image_anf import (
    ONE, ZERO, clause_violation_polynomial,
)


class AnfClauseRustTests(unittest.TestCase):
    def test_edge_cases(self):
        cases = ((), (1,), (-1,), (1, -1), (-1, -2),
                 (1, 1), (1, 2, 1), (300, -301),
                 (1, -1, 2), (1, -1, -2))
        for clause in cases:
            with self.subTest(clause=clause):
                self.assertEqual(clause_violation_polynomial(clause, backend="rust"),
                                 clause_violation_polynomial(clause))
        self.assertEqual(clause_violation_polynomial((), backend="rust"), ONE)
        self.assertEqual(clause_violation_polynomial((1, -1), backend="rust"), ZERO)

    def test_seeded_mixed_clauses(self):
        rng = random.Random(20261126)
        for index in range(400):
            n = rng.choice((3, 7, 17, 130, 301))
            clause = [rng.choice((-1, 1)) * rng.randint(1, n)
                      for _ in range(rng.randrange(8))]
            with self.subTest(index=index):
                self.assertEqual(clause_violation_polynomial(clause, backend="rust"),
                                 clause_violation_polynomial(clause))

    def test_zero_literal(self):
        for backend in ("python", "rust"):
            with self.subTest(backend=backend):
                with self.assertRaises(ValueError):
                    clause_violation_polynomial((1, -1, 0), backend=backend)


if __name__ == "__main__":
    unittest.main()
