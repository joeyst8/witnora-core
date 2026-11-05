"""Check numeric Lean emission and safety of source generation."""
import unittest

from witnora_core.lean_numeric_certificate_export import emit_numeric_lean


class NumericLeanExportTests(unittest.TestCase):
    def test_deterministic_cases(self):
        text = emit_numeric_lean()
        self.assertEqual(text, emit_numeric_lean())
        for name in ("triangle", "pathFour", "cliqueFour", "twoTriangles"):
            self.assertIn(f"{name}NumericPasses", text)
            self.assertIn(f"{name}NumericOptimal", text)
        self.assertIn("checkNumeric", text)
        self.assertIn("checked_numeric_sound", text)

    def test_duplicate_and_invalid_case(self):
        case = ("single", 1, (), [0], (0,))
        with self.assertRaises(ValueError):
            emit_numeric_lean((case, case))
        with self.assertRaises(ValueError):
            emit_numeric_lean((("bad-name", 1, (), [0], (0,)),))
        with self.assertRaises(ValueError):
            emit_numeric_lean((("bad", 2, ((0, 1),), [0, 0], (0, 1)),))


if __name__ == "__main__":
    unittest.main()
