import copy
import unittest

from witnora_core.bce import blocked_clause_proof
from witnora_core.certificate import CollapsePath, CollapseStep
from witnora_core.cnf import CNFFormula, Clause, formula_satisfied
from witnora_core.components import connected_components
from witnora_core.dimacs import parse_dimacs
from witnora_core.reconstruction import reconstruct_bce_step, reconstruct_ve_step
from witnora_core.runner import solve
from witnora_core.verifier import verify_collapse_path


def bce_demo_formula():
    return CNFFormula.from_raw_clauses([[1, 2, 3], [-1, -2], [-1, -3]])


def treewidth_demo_formula():
    return CNFFormula.from_raw_clauses(
        [[-3, -1], [-4, -3, 2], [-5, -4], [2, 3], [-2, 5], [1, 4]]
    )


def fake_bce_path(formula: CNFFormula, output: CNFFormula) -> CollapsePath:
    step = CollapseStep(
        step_id=1,
        type="BCE",
        input_formula_hash=formula.formula_hash,
        output_formula_hash=output.formula_hash,
        details={
            "removed_clause": [1, 2, 3],
            "blocked_literal": 1,
            "checked_resolvents": [],
            "proof_digest": "fake",
        },
        removed_clauses=[[1, 2, 3]],
        reconstruction_data={
            "removed_clause": [1, 2, 3],
            "blocked_literal": 1,
            "opposite_clauses": [[-1, 4]],
        },
    )
    return CollapsePath(
        original_formula_hash=formula.formula_hash,
        c_parameter=2,
        steps=[step],
        final_formula_hash=output.formula_hash,
        final_class="UNRESOLVED",
        status="NO_COLLAPSE_FOUND_UNDER_CURRENT_GRAMMAR_AND_C",
    )


class AdversarialCorrectnessTest(unittest.TestCase):
    def test_non_blocked_clause_not_removed(self):
        formula = CNFFormula.from_raw_clauses([[1, 2, 3], [-1, 4], [-2, -3]])
        clause = Clause([1, 2, 3])
        self.assertIsNone(blocked_clause_proof(formula, clause, 1))
        result = solve(formula, c=2)
        self.assertFalse(
            any(
                step.type == "BCE"
                and step.removed_clauses == [[1, 2, 3]]
                and step.details.get("blocked_literal") == 1
                for step in result.steps
            )
        )
        fake = fake_bce_path(formula, formula.without_clause(clause))
        self.assertFalse(verify_collapse_path(formula, fake).ok)
        print("NON_BLOCKED_BCE_REJECT_PASS")

    def test_bce_forced_repair(self):
        formula = bce_demo_formula()
        result = solve(formula, c=2)
        bce_step = next(step for step in result.steps if step.type == "BCE")
        repaired = reconstruct_bce_step({1: False, 2: False, 3: False}, bce_step)
        self.assertTrue(repaired.ok, repaired.error)
        self.assertTrue(repaired.assignment[1])
        self.assertTrue(formula_satisfied(formula, repaired.assignment))
        print("BCE_FORCED_REPAIR_PASS")

    def test_ve_reconstruction_sign_rule(self):
        positive_step = CollapseStep(
            step_id=1,
            type="VE",
            input_formula_hash="in",
            output_formula_hash="out",
            reconstruction_data={"eliminated_variable": 1, "removed_clauses": [[1, 2]]},
        )
        positive = reconstruct_ve_step({2: False}, positive_step)
        self.assertTrue(positive.ok, positive.error)
        self.assertTrue(positive.assignment[1])

        negative_step = CollapseStep(
            step_id=1,
            type="VE",
            input_formula_hash="in",
            output_formula_hash="out",
            reconstruction_data={"eliminated_variable": 1, "removed_clauses": [[-1, 2]]},
        )
        negative = reconstruct_ve_step({2: False}, negative_step)
        self.assertTrue(negative.ok, negative.error)
        self.assertFalse(negative.assignment[1])
        print("VE_SIGN_RECONSTRUCTION_PASS")

    def test_ve_reconstruction_conflict_detection(self):
        step = CollapseStep(
            step_id=1,
            type="VE",
            input_formula_hash="in",
            output_formula_hash="out",
            reconstruction_data={
                "eliminated_variable": 1,
                "removed_clauses": [[1, 2], [-1, 3]],
            },
        )
        result = reconstruct_ve_step({2: False, 3: False}, step)
        self.assertFalse(result.ok)
        self.assertIn("conflict", result.error)
        print("VE_CONFLICT_DETECTION_PASS")

    def test_cross_component_split_rejected(self):
        formula = CNFFormula.from_raw_clauses([[1, 2], [3, 4], [2, 3]])
        self.assertEqual(len(connected_components(formula)), 1)
        step = CollapseStep(
            step_id=1,
            type="CD",
            input_formula_hash=formula.formula_hash,
            output_formula_hash=formula.formula_hash,
            details={
                "component_count": 2,
                "incidence_edges": [[1, 0], [2, 0], [3, 1], [4, 1], [2, 2], [3, 2]],
                "components": [
                    {
                        "component_id": "0",
                        "formula_hash": CNFFormula.from_raw_clauses([[1, 2]]).formula_hash,
                        "variables": [1, 2],
                        "clauses": [[1, 2]],
                        "clause_indices": [0],
                    },
                    {
                        "component_id": "1",
                        "formula_hash": CNFFormula.from_raw_clauses([[3, 4]]).formula_hash,
                        "variables": [3, 4],
                        "clauses": [[3, 4]],
                        "clause_indices": [1],
                    },
                ],
                "parent_component_id": None,
            },
        )
        path = CollapsePath(
            original_formula_hash=formula.formula_hash,
            c_parameter=2,
            steps=[step],
            final_formula_hash=formula.formula_hash,
            final_class="UNRESOLVED",
            status="NO_COLLAPSE_FOUND_UNDER_CURRENT_GRAMMAR_AND_C",
        )
        self.assertFalse(verify_collapse_path(formula, path).ok)
        print("CROSS_COMPONENT_SPLIT_REJECT_PASS")

    def test_empty_formula_sat(self):
        formula = CNFFormula.from_raw_clauses([])
        result = solve(formula, c=0)
        self.assertEqual(result.status, "SAT")
        self.assertTrue(result.original_verification)
        print("EMPTY_FORMULA_SAT_PASS")

    def test_tautology_normalization(self):
        formula = CNFFormula.from_raw_clauses([[1, -1, 2], [2]])
        self.assertEqual(formula.to_clause_lists(), [[2]])
        result = solve(formula, c=2)
        self.assertEqual(result.status, "SAT")
        self.assertTrue(result.original_verification)
        self.assertTrue(formula_satisfied(formula, result.reconstructed_original_assignment))
        print("TAUTOLOGY_NORMALIZATION_PASS")

    def test_absent_dimacs_variable(self):
        formula = parse_dimacs("p cnf 5 1\n1 0\n")
        result = solve(formula, c=2)
        self.assertEqual(result.status, "SAT")
        self.assertTrue(result.original_verification)
        self.assertTrue(result.reconstructed_original_assignment[1])
        print("ABSENT_DIMACS_VARIABLE_PASS")

    def test_c_zero(self):
        formula = CNFFormula.from_raw_clauses([[1], [2]])
        result = solve(formula, c=0)
        self.assertEqual(result.status, "SAT")
        self.assertTrue(result.original_verification)
        self.assertFalse(any(step.type == "VE" for step in result.steps))
        print("C_ZERO_PASS")

    def test_no_brute_force_no_collapse(self):
        result = solve(treewidth_demo_formula(), c=1)
        self.assertEqual(result.status, "NO_COLLAPSE_FOUND_UNDER_CURRENT_GRAMMAR_AND_C")
        self.assertEqual(result.final_assignment, {})
        self.assertFalse(result.original_verification)
        print("NO_BRUTE_FORCE_NO_COLLAPSE_PASS")

    def test_verifier_negative_cases(self):
        formula = bce_demo_formula()
        valid = solve(formula, c=2)

        wrong_hash = copy.deepcopy(valid)
        wrong_hash.original_formula_hash = "0" * 64
        self.assertFalse(verify_collapse_path(formula, wrong_hash).ok)

        non_blocked = CNFFormula.from_raw_clauses([[1, 2, 3], [-1, 4], [-2, -3]])
        fake_bce = fake_bce_path(non_blocked, non_blocked.without_clause(Clause([1, 2, 3])))
        self.assertFalse(verify_collapse_path(non_blocked, fake_bce).ok)

        ve_formula = CNFFormula.from_raw_clauses([[1, 2], [-1, 3]])
        ve_output = CNFFormula.from_raw_clauses([[2, 3]])
        fake_ve_step = CollapseStep(
            step_id=1,
            type="VE",
            input_formula_hash=ve_formula.formula_hash,
            output_formula_hash=ve_output.formula_hash,
            removed_clauses=[[-1, 3], [1, 2]],
            added_clauses=[[2, -3]],
            reconstruction_data={
                "eliminated_variable": 1,
                "removed_clauses": [[-1, 3], [1, 2]],
                "added_resolvents": [[2, -3]],
            },
        )
        fake_ve = CollapsePath(
            original_formula_hash=ve_formula.formula_hash,
            c_parameter=2,
            steps=[fake_ve_step],
            final_formula_hash=ve_output.formula_hash,
            final_class="UNRESOLVED",
            status="NO_COLLAPSE_FOUND_UNDER_CURRENT_GRAMMAR_AND_C",
        )
        self.assertFalse(verify_collapse_path(ve_formula, fake_ve).ok)

        cross = CNFFormula.from_raw_clauses([[1, 2], [3, 4], [2, 3]])
        fake_cd_step = CollapseStep(
            step_id=1,
            type="CD",
            input_formula_hash=cross.formula_hash,
            output_formula_hash=cross.formula_hash,
            details={"component_count": 2, "incidence_edges": [], "components": []},
        )
        fake_cd = CollapsePath(
            original_formula_hash=cross.formula_hash,
            c_parameter=2,
            steps=[fake_cd_step],
            final_formula_hash=cross.formula_hash,
            final_class="UNRESOLVED",
            status="NO_COLLAPSE_FOUND_UNDER_CURRENT_GRAMMAR_AND_C",
        )
        self.assertFalse(verify_collapse_path(cross, fake_cd).ok)

        bad_assignment = copy.deepcopy(valid)
        bad_assignment.reconstructed_original_assignment = {1: False, 2: False, 3: False}
        bad_assignment.original_verification = True
        self.assertFalse(verify_collapse_path(formula, bad_assignment).ok)

        print("VERIFIER_NEGATIVE_TESTS_PASS")


if __name__ == "__main__":
    unittest.main()
