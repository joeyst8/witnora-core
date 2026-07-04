import unittest

from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.runner import solve
from witnora_core.verifier import verify_collapse_path


def multi_component_formula():
    return CNFFormula.from_raw_clauses(
        [
            [1, 2, 3],
            [-1, -2],
            [-1, -3],
            [4, 5],
            [-4, 5],
        ]
    )


def component_no_collapse_formula():
    return CNFFormula.from_raw_clauses(
        [
            [10, 11, 12],
            [-10, -11],
            [-10, -12],
            [-6, -4],
            [-7, -6, 5],
            [-8, -7],
            [5, 6],
            [-5, 8],
            [4, 7],
        ]
    )


class ComponentSolveTest(unittest.TestCase):
    def test_recursive_component_solving_and_merge(self):
        formula = multi_component_formula()
        result = solve(formula, c=2)
        self.assertEqual(result.status, "SAT")
        self.assertEqual(result.final_class, "COMPONENTS_SOLVED")
        self.assertTrue(result.original_verification)
        self.assertTrue(formula_satisfied(formula, result.reconstructed_original_assignment))
        self.assertEqual(len(result.component_results), 2)
        self.assertTrue(all(item["status"] == "SAT" for item in result.component_results))

        verification = verify_collapse_path(formula, result)
        self.assertTrue(verification.ok, verification.errors)

        cd_steps = [step for step in result.steps if step.type == "CD"]
        self.assertTrue(cd_steps)
        self.assertEqual(cd_steps[0].details["component_count"], 2)
        component_by_vars = {
            tuple(component["variables"]): component["component_id"]
            for component in cd_steps[0].details["components"]
        }
        bce_component_id = component_by_vars[(1, 2, 3)]
        two_sat_component_id = component_by_vars[(4, 5)]

        self.assertTrue(
            any(
                step.type == "BCE"
                and step.details.get("component_id") == bce_component_id
                and step.removed_clauses == [[1, 2, 3]]
                for step in result.steps
            )
        )
        self.assertTrue(
            any(
                step.type == "2SAT_SOLVE"
                and step.details.get("component_id") == two_sat_component_id
                and step.details.get("status") == "SAT"
                for step in result.steps
            )
        )
        print("COMPONENT_SOLVE_PASS")

    def test_component_no_collapse_is_not_partial_sat(self):
        formula = component_no_collapse_formula()
        result = solve(formula, c=1)
        self.assertEqual(result.status, "NO_COLLAPSE_FOUND_UNDER_CURRENT_GRAMMAR_AND_C")
        self.assertEqual(result.final_class, "UNRESOLVED")
        self.assertFalse(result.original_verification)
        self.assertEqual(result.final_assignment, {})
        self.assertTrue(result.component_results)
        self.assertTrue(
            any(
                item["status"] == "NO_COLLAPSE_FOUND_UNDER_CURRENT_GRAMMAR_AND_C"
                for item in result.component_results
            )
        )
        self.assertTrue(any(step.type == "BCE" for step in result.steps))
        self.assertNotIn("HARD", str(result.to_dict()))
        self.assertNotIn("UNKNOWN", str(result.to_dict()))
        print("COMPONENT_NO_COLLAPSE_PASS")


if __name__ == "__main__":
    unittest.main()
