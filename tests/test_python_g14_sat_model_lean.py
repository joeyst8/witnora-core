"""Python-to-Lean SAT residual fixture generation and mutation checks."""
import unittest

from scripts.generate_python_g14_sat_model_lean import emit_sat_model_transfer


class PythonG14SatModelLeanTests(unittest.TestCase):
    def test_emits_deterministically(self):
        one = emit_sat_model_transfer()
        self.assertEqual(one, emit_sat_model_transfer())
        self.assertIn("python_residual_models_iff", one)
        self.assertIn("python_wrong_branch_counterexample", one)
        self.assertIn("python_swapped_branch_rejected", one)
        self.assertNotIn("sorry", one)
        self.assertNotIn("native_decide", one)

    def test_separate_python_branch_requirements(self):
        source = emit_sat_model_transfer()
        self.assertIn("[(1, false)]", source)
        self.assertIn("[(1, true)]", source)
        self.assertIn("[(2, true)]", source)
        self.assertIn("[(3, true)]", source)
        self.assertIn("[(4, true)]", source)


if __name__ == "__main__":
    unittest.main()
