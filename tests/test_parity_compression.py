"""Bounded independent checks of root-offset parity compression."""
from itertools import combinations, product
import random
import unittest

from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.parity_compression import (
    compress_binary_xor_components, reconstruct_values,
    substitute_residual_formula,
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



    def test_residual_clause_rewrite_matches_reconstructed_assignments(self):
        rng = random.Random(71717)
        for n in range(3, 8):
            for _ in range(20):
                truth = {v: rng.randrange(2) for v in range(1, n + 1)}
                edges = [(u, v, truth[u] ^ truth[v])
                         for u, v in combinations(range(1, n + 1), 2)
                         if rng.random() < 0.45]
                base = formula_from_edges(edges)
                extras = [
                    [((1 if rng.randrange(2) else -1) * rng.randint(1, n))
                     for _ in range(rng.randint(1, 4))]
                    for _ in range(3)
                ]
                formula = CNFFormula.from_raw_clauses(
                    base.to_clause_lists() + extras)
                cert = compress_binary_xor_components(formula)
                self.assertEqual(cert["status"], "UNVERIFIED_STRUCTURAL_CANDIDATE")
                residual = substitute_residual_formula(formula, cert)
                root_ids = sorted(set(dict(cert["roots"]).values()))
                other_ids = sorted(set(formula.variables) - set(dict(cert["roots"])))
                choices = sorted(set(root_ids) | set(other_ids))
                for bits in product((0, 1), repeat=len(choices)):
                    roots = dict(zip(choices, bits))
                    lifted = reconstruct_values(cert, roots)
                    lifted.update({v: roots[v] for v in other_ids})
                    self.assertEqual(formula_satisfied(formula, lifted),
                                     formula_satisfied(residual, roots))

    def test_residual_preserves_sat_and_unsat_with_nonxor_units(self):
        for clause in ([1], [-1]):
            graph = formula_from_edges([(1, 2, 0), (2, 3, 1)])
            formula = CNFFormula.from_raw_clauses(
                graph.to_clause_lists() + [clause, [-clause[0]]])
            cert = compress_binary_xor_components(formula)
            residual = substitute_residual_formula(formula, cert)
            self.assertTrue(residual.contains_empty_clause or
                            not any(formula_satisfied(
                                residual, dict(zip(residual.variables, bits)))
                                for bits in product((0, 1), repeat=len(residual.variables))))

if __name__ == "__main__":
    unittest.main()
