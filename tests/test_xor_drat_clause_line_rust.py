"""R-139: DRAT line format differential, including signed and empty clauses."""
import random
import unittest

from witnora_core.xor_drat import _clause_line


class XorDratClauseLineRustTests(unittest.TestCase):
    def test_seeded_lines(self):
        rng = random.Random(139)
        for trial in range(200):
            clause = tuple(rng.sample(range(-200, 200), rng.randrange(0, 11)))
            with self.subTest(trial=trial):
                self.assertEqual(_clause_line(clause, backend="rust"),
                                 _clause_line(clause))


if __name__ == "__main__":
    unittest.main()
