"""R-128: exclude source witness from clauses overlapping XOR support."""
import random
import unittest

from witnora_core.xor import _extra_touching_clauses


class XorExtraTouchingRustTests(unittest.TestCase):
    def test_seeded_formula_overlaps(self):
        rng = random.Random(20261209)
        for trial in range(350):
            n = rng.choice((5, 13, 90, 160))
            clauses = set()
            for _ in range(rng.randrange(30)):
                clause = tuple(sorted(rng.choice((-1,1))*v for v in
                              rng.sample(range(1,n+1),rng.randrange(1, min(n,5)+1))))
                clauses.add(clause)
            source = set(rng.sample(sorted(clauses),rng.randrange(len(clauses)+1)))
            variables = tuple(sorted(rng.sample(range(1,n+1),
                                               rng.randrange(min(n,7)+1))))
            with self.subTest(trial=trial):
                self.assertEqual(_extra_touching_clauses(
                    clauses,variables,source,backend="rust"),
                    _extra_touching_clauses(clauses,variables,source))


if __name__ == "__main__":
    unittest.main()
