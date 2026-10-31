"""Checks for deterministic and guarded Python -> Lean graph emission."""
import unittest

from witnora_core.lean_color_certificate_export import (
    _validate, emit_lean, generate_default_cases, find_matching_clique,
)


class LeanColorCertificateExportTests(unittest.TestCase):
    def test_deterministic_generation(self):
        a = emit_lean()
        b = emit_lean()
        self.assertEqual(a, b)
        self.assertEqual(len(generate_default_cases()), 4)
        for token in ("trianglePasses", "pathFourPasses",
                      "cliqueFourPasses", "twoTrianglesPasses",
                      "checked_certificate_sound"):
            self.assertIn(token, a)

    def test_each_python_witness_valid(self):
        for name, n, edges, colors, clique in generate_default_cases():
            with self.subTest(name=name):
                self.assertEqual(_validate(n, edges, colors, clique),
                                 max(colors) + 1)

    def test_invalid_certificates_rejected_before_emission(self):
        with self.assertRaises(ValueError):
            _validate(3, ((0, 1),), [0, 0, 1], (0, 1))
        with self.assertRaises(ValueError):
            _validate(3, ((0, 1),), [0, 1, 0], (0, 2))
        with self.assertRaises(ValueError):
            _validate(3, ((0, 1), (0, 1)), [0, 1, 0], (0, 1))
        with self.assertRaises(ValueError):
            emit_lean((("bad-name", 1, (), [0], (0,)),))
        self.assertIsNone(find_matching_clique(5,
                          ((0, 1), (1, 2), (2, 3), (3, 4), (0, 4)), 3))


if __name__ == "__main__":
    unittest.main()
