import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.runner import solve


class NoCollapseTest(unittest.TestCase):
    def test_no_collapse_c1(self):
        formula = CNFFormula.from_raw_clauses(
            [[-3, -1], [-4, -3, 2], [-5, -4], [2, 3], [-2, 5], [1, 4]]
        )
        result = solve(formula, c=1)
        self.assertEqual(result.status, "NO_COLLAPSE_FOUND_UNDER_CURRENT_GRAMMAR_AND_C")
        self.assertEqual(result.final_class, "UNRESOLVED")
        self.assertFalse(result.original_verification)
        self.assertNotIn("HARD", str(result.to_dict()))
        self.assertNotIn("UNKNOWN", str(result.to_dict()))
        print("NO_COLLAPSE_PASS")


if __name__ == "__main__":
    unittest.main()
