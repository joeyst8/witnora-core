import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.runner import solve


class DeterminismTest(unittest.TestCase):
    def test_deterministic_path_and_assignment(self):
        formula = CNFFormula.from_raw_clauses([[1, 2, 3], [-1, -2], [-1, -3]])
        first = solve(formula, c=2).to_dict()
        second = solve(formula, c=2).to_dict()

        self.assertEqual(first["certificate_hash"], second["certificate_hash"])
        self.assertEqual(first["original_formula_hash"], second["original_formula_hash"])
        self.assertEqual(first["collapse_path"], second["collapse_path"])
        self.assertEqual(first["status"], second["status"])
        self.assertEqual(
            first["reconstructed_original_assignment"],
            second["reconstructed_original_assignment"],
        )
        print("DETERMINISM_PASS")


if __name__ == "__main__":
    unittest.main()
