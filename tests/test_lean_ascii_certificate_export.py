"""Adversarial and deterministic tests for Python ASCII certificate emitter."""
import unittest

from witnora_core.lean_ascii_certificate_export import (
    emit_ascii_lean, serialize_ascii_certificate,
)


class AsciiLeanCertificateTests(unittest.TestCase):
    def test_determinism(self):
        source = emit_ascii_lean()
        self.assertEqual(source, emit_ascii_lean())
        for name in ("triangle", "pathFour", "cliqueFour", "twoTriangles"):
            self.assertIn(f"{name}AsciiPasses", source)
            self.assertIn(f"{name}AsciiDamagedRejects", source)
            self.assertIn(f"{name}AsciiOptimal", source)
        self.assertNotIn("native_decide", source)

    def test_known_triangle_bytes(self):
        self.assertEqual(
            serialize_ascii_certificate(
                3, ((0, 1), (0, 2), (1, 2)), [0, 1, 2], (0, 1, 2)),
            b"2|2|0,1;0,2;1,2|0,1,2|0,1,2",
        )

    def test_invalid_case_is_rejected(self):
        with self.assertRaises(ValueError):
            serialize_ascii_certificate(2, ((0, 1),), [0, 0], (0, 1))
        case = ("one", 1, (), [0], (0,))
        with self.assertRaises(ValueError):
            emit_ascii_lean((case, case))
        with self.assertRaises(ValueError):
            emit_ascii_lean((("invalid-name", 1, (), [0], (0,)),))


if __name__ == "__main__":
    unittest.main()
