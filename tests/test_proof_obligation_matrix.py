import unittest

from witnora_core.hierarchy_formalization import proof_obligation_matrix


class ProofObligationMatrixTest(unittest.TestCase):
    def test_proof_obligation_matrix(self):
        matrix = proof_obligation_matrix()
        types = {row.obligation_type for row in matrix}
        required = {
            "PRIOR_GRAMMAR_NON_COLLAPSE",
            "NEW_GRAMMAR_CERTIFICATION",
            "CHECKER_SOUNDNESS",
            "BOUND_PROFILE_WELL_DEFINED",
            "COST_MODEL_COMPLETE",
            "WITNESS_FAMILY_SCALING",
            "LOWER_BOUND_REQUIRED",
            "DRAT_BRIDGE_OPTIONAL",
            "NATIVE_CERTIFICATE_SOUNDNESS",
        }
        self.assertTrue(required.issubset(types))
        statuses = {row.current_status for row in matrix}
        self.assertTrue(statuses.issubset({"SATISFIED_BY_TESTS", "SATISFIED_BY_CHECKER", "FORMAL_PROOF_SKETCH_ONLY", "OPEN", "NOT_ATTEMPTED"}))
        print("PROOF_OBLIGATION_MATRIX_PASS")


if __name__ == "__main__":
    unittest.main()

