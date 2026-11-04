"""R-093: exact Python/Rust Lean numeric source parity; Lean remains checker."""
import unittest

from witnora_core.lean_numeric_certificate_export import emit_numeric_lean
from witnora_core.lean_color_certificate_export import generate_default_cases

try:
    from witnora_ve import lean_numeric_emit_native
except ImportError:
    lean_numeric_emit_native = None


@unittest.skipUnless(lean_numeric_emit_native is not None, "native wheel unavailable")
class NumericLeanExporterRust(unittest.TestCase):
    def test_exact_default_and_permutations(self):
        cases = list(generate_default_cases())
        for count in range(5):
            with self.subTest(count=count):
                selected = tuple(cases[:count])
                self.assertEqual(emit_numeric_lean(selected),
                                 emit_numeric_lean(selected, backend="rust"))
        for shift in range(len(cases)):
            shuffled = tuple(cases[shift:] + cases[:shift])
            self.assertEqual(emit_numeric_lean(shuffled),
                             emit_numeric_lean(shuffled, backend="rust"))

    def test_invalid_cases_same_errors(self):
        case = generate_default_cases()[0]
        invalid = ((case, case), (("bad-name", 1, (), [0], (0,)),),
                   (("bad", 2, ((0, 1),), [0, 0], (0, 1)),))
        for cases in invalid:
            for backend in ("python", "rust"):
                with self.subTest(backend=backend):
                    with self.assertRaises(ValueError):
                        emit_numeric_lean(cases, backend=backend)


if __name__ == "__main__":
    unittest.main()
