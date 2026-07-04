import unittest

from witnora_core.certificate import SAT
from witnora_core.cnf import CNFFormula
from witnora_core.primal import primal_graph
from witnora_core.runner import solve
from witnora_core.treewidth import find_elimination_order, verify_elimination_order


def treewidth_formula():
    return CNFFormula.from_raw_clauses(
        [[-3, -1], [-4, -3, 2], [-5, -4], [2, 3], [-2, 5], [1, 4]]
    )


class TreewidthDemoTest(unittest.TestCase):
    def test_treewidth_collapse(self):
        formula = treewidth_formula()
        self.assertFalse(formula.is_2cnf)
        graph = primal_graph(formula)
        order = find_elimination_order(graph, 2)
        self.assertIsNotNone(order)
        self.assertLessEqual(verify_elimination_order(graph, order), 2)

        result = solve(formula, c=2)
        self.assertEqual(result.status, SAT)
        self.assertTrue(result.original_verification)
        self.assertTrue(any(step.type == "TREEWIDTH_SOLVE" for step in result.steps))
        self.assertFalse(
            any(step.type == "BCE" and step.removed_clauses == [[-4, -3, 2]] for step in result.steps)
        )
        print("TREEWIDTH_COLLAPSE_PASS")


if __name__ == "__main__":
    unittest.main()
