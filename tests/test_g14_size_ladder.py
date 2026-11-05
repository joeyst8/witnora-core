"""Check increasing G14 family cases and independent native certificates."""
import unittest

from witnora_core.python_g14_lean_artifact import (
    actual_python_g14_artifacts, emit_python_g14_lean,
)
from witnora_core.operator_genesis import AFFINE_RESIDUE_CERTIFICATE_VERIFIED


class G14SizeLadderTests(unittest.TestCase):
    def test_multiple_component_sizes(self):
        counts = []
        for n in (2, 3, 4):
            name = f"saf_unsat_cover_{n}"
            formula, branches = actual_python_g14_artifacts(name)
            self.assertEqual(len(branches), 2)
            self.assertGreater(formula.num_clauses, 0)
            counts.append(formula.num_clauses)
            selected = []
            for assignment, residual, parts, chosen, cert in branches:
                self.assertEqual(len(parts), n)
                self.assertIn(chosen, parts)
                self.assertEqual(cert.checker_status,
                                 AFFINE_RESIDUE_CERTIFICATE_VERIFIED)
                self.assertTrue(cert.row_operations)
                selected.append(tuple(chosen.variables))
            self.assertNotEqual(selected[0], selected[1])
            lean = emit_python_g14_lean(name)
            self.assertIn("python_g14_g5_dimacs_unsat", lean)
            self.assertIn("python_selected_strict_affine_rejected", lean)
            self.assertIn("python_selected_semantic_affine_pass", lean)
            self.assertIn("python_all_component_lengths_pass", lean)
            self.assertIn("python_all_components_semantic_affine_pass", lean)
            self.assertIn("python_missing_component_rejected", lean)
            self.assertIn("python_invalid_g5_reference_rejected", lean)
        self.assertEqual(counts, sorted(counts))
        self.assertEqual(len(set(counts)), 3)


if __name__ == "__main__":
    unittest.main()
