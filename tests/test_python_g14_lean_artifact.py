"""Check the Python conditioning, partitions, and emitted Lean source."""
import unittest

from witnora_core.python_g14_lean_artifact import (
    actual_python_g14_artifacts, emit_python_g14_lean,
)


class PythonG14ArtifactTests(unittest.TestCase):
    def test_python_branches_and_residuals(self):
        formula, branches = actual_python_g14_artifacts()
        self.assertEqual(formula.num_clauses, 3)
        self.assertEqual([assignment for assignment, *_ in branches],
                         [{1: False}, {1: True}])
        for assignment, residual, parts, chosen, units in branches:
            self.assertEqual(residual, chosen)
            self.assertEqual(parts, [chosen])
            self.assertEqual({row[0] for row in units}, {-2, 2})

    def test_deterministic_lean_generation(self):
        source = emit_python_g14_lean()
        self.assertEqual(source, emit_python_g14_lean())
        for theorem in ("python_document_passes", "python_partitions_pass",
                        "python_g5_pass", "python_g14_g5_dimacs_unsat"):
            self.assertIn(theorem, source)
        self.assertNotIn("native_decide", source)


if __name__ == "__main__":
    unittest.main()
