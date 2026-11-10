"""Local tests for the WU-014 independent XNF SAT-model validator."""

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import wu014_real_solver_pilot as pilot


class TestPilotModelValidation(unittest.TestCase):
    def test_xnf_two_lineral_clause_satisfied_by_model(self):
        clauses = [(((1, 2), False), ((3,), True)),
                   (((1, 3), True), ((2,), False))]
        self.assertTrue(pilot.check_model(3, clauses, {1: True, 2: True, 3: False}))
        self.assertFalse(pilot.check_model(3, clauses, {1: False, 2: False, 3: True}))
        self.assertFalse(pilot.check_model(3, clauses, {1: True, 2: False}))

    def test_sat_and_unsat_output_schemas(self):
        sat, model = pilot.read_solution("s SATISFIABLE\nv 1 -2 3 0\n", 3)
        self.assertEqual(sat, "SAT")
        self.assertEqual(model, {1: True, 2: False, 3: True})
        self.assertEqual(pilot.read_solution("s UNSATISFIABLE\n", 3), ("UNSAT", {}))
        with self.assertRaises(ValueError):
            pilot.read_solution("s SATISFIABLE\ns UNSATISFIABLE\n", 3)
        with self.assertRaises(ValueError):
            pilot.read_solution("s SATISFIABLE\nv 1 -1 0\n", 3)


if __name__ == "__main__":
    unittest.main()
