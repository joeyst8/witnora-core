"""R-094: exact ASCII bytes/Lean source parity against Python."""
import random
import unittest

from witnora_core.lean_ascii_certificate_export import (
    emit_ascii_lean, lean_bytes, serialize_ascii_certificate,
)
from witnora_core.lean_color_certificate_export import generate_default_cases

try:
    from witnora_ve import lean_ascii_emit_native
except ImportError:
    lean_ascii_emit_native = None


@unittest.skipUnless(lean_ascii_emit_native is not None, "native wheel unavailable")
class AsciiLeanExporterRust(unittest.TestCase):
    def test_source_text_exact(self):
        cases = list(generate_default_cases())
        for count in range(len(cases) + 1):
            selected = tuple(cases[:count])
            self.assertEqual(emit_ascii_lean(selected), emit_ascii_lean(selected, backend="rust"))
        for rotation in range(len(cases)):
            selected = tuple(cases[rotation:] + cases[:rotation])
            self.assertEqual(emit_ascii_lean(selected), emit_ascii_lean(selected, backend="rust"))

    def test_bytes_and_wire(self):
        rng = random.Random(94094)
        for _ in range(200):
            raw = bytes(rng.randrange(256) for _ in range(rng.randrange(0, 100)))
            self.assertEqual(lean_bytes(raw), lean_bytes(raw, backend="rust"))
        for _, n, edges, colors, clique in generate_default_cases():
            self.assertEqual(serialize_ascii_certificate(n, edges, colors, clique),
                             serialize_ascii_certificate(n, edges, colors, clique, backend="rust"))

    def test_validation_matches(self):
        case = generate_default_cases()[0]
        invalid = ((case, case), (("invalid-name", 1, (), [0], (0,)),),
                   (("bad", 2, ((0, 1),), [0, 0], (0, 1)),))
        for cases in invalid:
            for backend in ("python", "rust"):
                with self.subTest(backend=backend):
                    with self.assertRaises(ValueError):
                        emit_ascii_lean(cases, backend=backend)


if __name__ == "__main__":
    unittest.main()
