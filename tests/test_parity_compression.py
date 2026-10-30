"""Bounded independent checks of root-offset parity compression."""
from itertools import combinations, product
import random
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.parity_compression import (
    compress_binary_xor_components, reconstruct_values,
)
from witnora_core.xor import canonical_xor_cnf_clauses


def formula_from_edges(edges):
    clauses = set()
    for u, v, rhs in edges:
        clauses.update(canonical_xor_cnf_clauses((u, v), rhs))
    return CNFFormula.from_raw_clauses(clauses)


class ParityCompressionTest(unittest.TestCase):
    def test_random_consistent_graphs(self):
        rng = random.Random(71319)
        for n in range(3, 9):
            for _ in range(25):
                truth = {i: rng.randrange(2) for i in range(1, n+1)}
                edges = [
                    (u, v, truth[u] ^ truth[v])
                    for u, v in combinations(range(1, n+1), 2)
                    if rng.random() < 0.38
                ]
                cert = compress_binary_xor_components(formula_from_edges(edges))
                self.assertEqual(cert["status"], "UNVERIFIED_STRUCTURAL_CANDIDATE")
                self.assertEqual(cert["root_variables_saved"],
                                 cert["input_vertices"] - cert["component_count"])
                root_ids = sorted(set(dict(cert["roots"]).values()))
                for bits in product((0, 1), repeat=len(root_ids)):
                    values = reconstruct_values(cert, dict(zip(root_ids, bits)))
                    self.assertTrue(all(values[u] ^ values[v] == rhs
                                        for u, v, rhs in edges))

    def test_odd_triangle_rejected(self):
        f = formula_from_edges([(1, 2, 0), (2, 3, 0), (1, 3, 1)])
        cert = compress_binary_xor_components(f)
        self.assertEqual(cert["status"], "INCONSISTENT_XOR_EQUATIONS")
        with self.assertRaises(ValueError):
            reconstruct_values(cert, {1: 0})

    def test_non_xor_clauses_remain_outside_contract(self):
        f = CNFFormula.from_raw_clauses([[1], [-1]])
        cert = compress_binary_xor_components(f)
        self.assertEqual(cert["input_vertices"], 0)
        self.assertEqual(cert["claim_boundary"],
                         "only extracted binary XOR constraints; arbitrary CNF residual is untouched")


if __name__ == "__main__":
    unittest.main()
