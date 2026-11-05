"""R-143/R-144: source-row encoding and values agree exactly with Python."""
import random
import unittest

from witnora_core.xor import XorEquation
from witnora_core.xor_drat import _source_row_encodings, _source_row_values


class XorRowSourcesRustTests(unittest.TestCase):
    def test_random_source_rows(self):
        rng = random.Random(143144)
        for trial in range(180):
            equations = []
            for _ in range(rng.randrange(0, 12)):
                variables = rng.sample(range(1, 9), rng.randrange(0, 6))
                clauses = [rng.sample(range(-8, 0), rng.randrange(0, 4))
                           for _ in range(rng.randrange(0, 7))]
                equations.append(XorEquation(variables, rng.randrange(2),
                                             source_clauses=clauses))
            with self.subTest(trial=trial):
                self.assertEqual(_source_row_encodings(equations, backend="rust"),
                                 _source_row_encodings(equations))
                self.assertEqual(_source_row_values(equations, backend="rust"),
                                 _source_row_values(equations))


if __name__ == "__main__":
    unittest.main()
