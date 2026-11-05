import json
import unittest
from itertools import combinations

from witnora_core.certificate import SAT
from witnora_core.cnf import CNFFormula, Clause, formula_satisfied
from witnora_core.families import make_blocked_clique_collapse_family
from witnora_core.primal import primal_graph
from witnora_core.runner import solve
from witnora_core.treewidth import find_elimination_order, verify_elimination_order


def blocked_clique_long_clause(n):
    return Clause(range(1, n + 2))


def blocked_clique_after_bce_formula(n):
    return CNFFormula.from_raw_clauses([[-1, -(i + 1)] for i in range(1, n + 1)])


class StrictnessFamilyTest(unittest.TestCase):
    def test_blocked_clique_collapse(self):
        n = 6
        formula = make_blocked_clique_collapse_family(n)
        long_clause = blocked_clique_long_clause(n)

        self.assertIn(long_clause, formula.clauses)
        self.assertEqual(len(long_clause), n + 1)

        graph = primal_graph(formula)
        clique_vertices = list(range(1, n + 2))
        for a, b in combinations(clique_vertices, 2):
            self.assertIn(b, graph[a])
            self.assertIn(a, graph[b])

        result = solve(formula, c=1)
        self.assertEqual(result.status, SAT)
        self.assertTrue(result.original_verification)
        self.assertTrue(formula_satisfied(formula, result.reconstructed_original_assignment))

        self.assertTrue(
            any(
                step.type == "BCE"
                and step.removed_clauses == [long_clause.to_list()]
                and step.details["blocked_literal"] == 1
                for step in result.steps
            )
        )
        print("BLOCKED_CLIQUE_COLLAPSE_PASS")

    def test_strictness_treewidth_signal(self):
        n = 6
        formula = make_blocked_clique_collapse_family(n)
        graph = primal_graph(formula)
        clique_vertices = list(range(1, n + 2))

        for a, b in combinations(clique_vertices, 2):
            self.assertIn(b, graph[a])
        clique_lower_bound = len(clique_vertices) - 1
        self.assertGreaterEqual(clique_lower_bound, n)

        after_bce = blocked_clique_after_bce_formula(n)
        after_bce_graph = primal_graph(after_bce)
        order = find_elimination_order(after_bce_graph, 1)
        self.assertIsNotNone(order)
        self.assertLessEqual(verify_elimination_order(after_bce_graph, order), 1)
        print("STRICTNESS_TREEWIDTH_SIGNAL_PASS")

    def test_family_scaling(self):
        for n in [3, 5, 8, 10]:
            formula = make_blocked_clique_collapse_family(n)
            first = solve(formula, c=1)
            second = solve(formula, c=1)

            self.assertEqual(first.status, SAT)
            self.assertTrue(first.original_verification)
            self.assertTrue(formula_satisfied(formula, first.reconstructed_original_assignment))
            self.assertEqual(first.certificate_hash, second.certificate_hash)
            self.assertNotIn("BRUTE", json.dumps(first.to_dict()).upper())
        print("FAMILY_SCALING_PASS")


if __name__ == "__main__":
    unittest.main()
