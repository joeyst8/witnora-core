"""R-147/R-148: exact parity gadget encoding and source-CNF union."""
import random
import unittest

from witnora_core.xor import XorEquation
from witnora_core.xor_drat import _source_clauses, _xor_encoding_clauses


class XorSourceUnionRustTests(unittest.TestCase):
    def test_seeded_full_encoding(self):
        rng = random.Random(147)
        for trial in range(200):
            variables = rng.sample(range(1, 14), rng.randrange(0, 8))
            rhs = rng.randrange(4)
            with self.subTest(trial=trial):
                self.assertEqual(_xor_encoding_clauses(variables, rhs, backend="rust"),
                                 _xor_encoding_clauses(variables, rhs))

    def test_source_union(self):
        rng = random.Random(148)
        for trial in range(250):
            rows = []
            for _ in range(rng.randrange(0, 10)):
                clauses = [rng.sample(range(-12, 0), rng.randrange(0, 5))
                           for _ in range(rng.randrange(0, 10))]
                rows.append(XorEquation([1, 2], rng.randrange(2), source_clauses=clauses))
            with self.subTest(trial=trial):
                self.assertEqual(_source_clauses(rows, backend="rust"),
                                 _source_clauses(rows))


if __name__ == "__main__":
    unittest.main()
