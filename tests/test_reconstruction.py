import unittest

from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.runner import solve


class ReconstructionTest(unittest.TestCase):
    def test_sat_reconstructions_verify_original(self):
        formulas = [
            CNFFormula.from_raw_clauses([[1, 2, 3], [-1, -2], [-1, -3]]),
            CNFFormula.from_raw_clauses(
                [[-3, -1], [-4, -3, 2], [-5, -4], [2, 3], [-2, 5], [1, 4]]
            ),
        ]
        for formula in formulas:
            result = solve(formula, c=2)
            self.assertEqual(result.status, "SAT")
            self.assertTrue(result.original_verification)
            self.assertTrue(formula_satisfied(formula, result.reconstructed_original_assignment))
        print("RECONSTRUCTION_PASS")


if __name__ == "__main__":
    unittest.main()
