"""R-074 full native root-offset compression, reconstruct and residual parity."""
from itertools import combinations
import random
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.xor import canonical_xor_cnf_clauses
from witnora_core.parity_compression import (
    compress_binary_xor_components, reconstruct_values,
    substitute_residual_formula,
)


def from_edges(edges):
    clauses = set()
    for a, b, rhs in edges:
        clauses.update(canonical_xor_cnf_clauses((a, b), rhs))
    return CNFFormula.from_raw_clauses(clauses)


class ParityCompressionRustTests(unittest.TestCase):
    def setUp(self):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            self.skipTest("native Rust wheel not installed")

    def test_300_random_full_reports_and_residuals(self):
        rng = random.Random(74074)
        for trial in range(300):
            n = rng.randrange(3, 13)
            truth = {i: rng.randrange(2) for i in range(1, n + 1)}
            edges = [(u, v, truth[u] ^ truth[v])
                     for u, v in combinations(range(1, n + 1), 2)
                     if rng.randrange(4) == 0]
            source = from_edges(edges)
            extras = [[rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                       for _ in range(rng.randrange(1, 5))]
                      for _ in range(4)]
            source = CNFFormula.from_raw_clauses(source.to_clause_lists() + extras)
            with self.subTest(trial=trial):
                expected = compress_binary_xor_components(source)
                got = compress_binary_xor_components(source, backend="rust")
                self.assertEqual(got, expected)
                if got["status"] == "UNVERIFIED_STRUCTURAL_CANDIDATE":
                    root_ids = set(dict(got["roots"]).values())
                    values = {r: rng.randrange(2) for r in root_ids}
                    self.assertEqual(reconstruct_values(got, values, backend="rust"),
                                     reconstruct_values(expected, values))
                    self.assertEqual(substitute_residual_formula(source, got, backend="rust"),
                                     substitute_residual_formula(source, expected))

    def test_inconsistent_cycles_and_empty_cases(self):
        cases = [CNFFormula(), CNFFormula.from_raw_clauses([[1], [-1]]),
                 from_edges([(1, 2, 0), (2, 3, 0), (1, 3, 1)]),
                 from_edges([(1, 2, 1), (2, 3, 0), (1, 3, 1)])]
        for source in cases:
            self.assertEqual(compress_binary_xor_components(source, backend="rust"),
                             compress_binary_xor_components(source))
        with self.assertRaises(ValueError):
            compress_binary_xor_components(CNFFormula(), backend="unknown")


if __name__ == "__main__":
    unittest.main()
