import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.runner import solve


class UnsatTest(unittest.TestCase):
    def test_unit_conflict(self):
        result = solve(CNFFormula.from_raw_clauses([[1], [-1]]), c=2)
        self.assertEqual(result.status, "UNSAT")
        self.assertEqual(result.final_class, "CONFLICT")
        self.assertTrue(any(step.type == "UP" for step in result.steps))
        print("UNSAT_PASS")


if __name__ == "__main__":
    unittest.main()
