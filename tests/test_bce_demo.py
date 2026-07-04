import unittest

from witnora_core.certificate import SAT
from witnora_core.cnf import CNFFormula, Clause, formula_satisfied
from witnora_core.reconstruction import reconstruct_bce_step
from witnora_core.runner import solve


def bce_formula():
    return CNFFormula.from_raw_clauses([[1, 2, 3], [-1, -2], [-1, -3]])


class BCEDemoTest(unittest.TestCase):
    def test_bce_demo_and_reconstruction_rule(self):
        result = solve(bce_formula(), c=2)
        data = result.to_dict()
        self.assertEqual(data["status"], SAT)
        self.assertTrue(data["original_verification"])

        bce_steps = [step for step in result.steps if step.type == "BCE"]
        self.assertTrue(bce_steps)
        step = bce_steps[0]
        self.assertEqual(step.removed_clauses, [[1, 2, 3]])
        self.assertEqual(step.details["blocked_literal"], 1)

        reduced_assignment = {1: False, 2: False, 3: False}
        reconstructed = reconstruct_bce_step(reduced_assignment, step)
        self.assertTrue(reconstructed.ok, reconstructed.error)
        self.assertTrue(reconstructed.assignment[1])

        clauses = [Clause([1, 2, 3]), Clause([-1, -2]), Clause([-1, -3])]
        for clause in clauses:
            self.assertTrue(any((lit > 0) == reconstructed.assignment[abs(lit)] for lit in clause))
        print("BCE_RECONSTRUCTION_PASS")


if __name__ == "__main__":
    unittest.main()
