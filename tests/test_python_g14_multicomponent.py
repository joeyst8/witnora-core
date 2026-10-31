"""Guarded two-component G14 native G5 trace integration tests."""
import unittest

from witnora_core.python_g14_lean_artifact import (
    actual_python_g14_artifacts, emit_python_g14_lean,
)
from witnora_core.operator_genesis import AFFINE_RESIDUE_CERTIFICATE_VERIFIED


class MultiComponentG14Tests(unittest.TestCase):
    def test_cover_uses_different_native_components(self):
        formula, branches = actual_python_g14_artifacts("saf_unsat_cover_2")
        self.assertGreater(formula.num_clauses, 8)
        self.assertEqual(len(branches), 2)
        chosen_variable_sets = []
        for assignment, residual, parts, chosen, certificate in branches:
            self.assertEqual(len(parts), 2)
            self.assertIn(chosen, parts)
            self.assertEqual(certificate.checker_status,
                             AFFINE_RESIDUE_CERTIFICATE_VERIFIED)
            self.assertTrue(certificate.row_operations)
            self.assertEqual(certificate.gaussian_elimination_trace[0]["type"],
                             "INITIAL_ROWS")
            chosen_variable_sets.append(tuple(chosen.variables))
        self.assertNotEqual(chosen_variable_sets[0], chosen_variable_sets[1])

    def test_deterministic_emission(self):
        source = emit_python_g14_lean("saf_unsat_cover_2")
        self.assertEqual(source, emit_python_g14_lean("saf_unsat_cover_2"))
        self.assertIn("python_g14_g5_dimacs_unsat", source)
        self.assertIn("python_g5_pass", source)
        self.assertNotIn("native_decide", source)


if __name__ == "__main__":
    unittest.main()
