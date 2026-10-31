"""Compare Python XOR encoder clauses with deterministic DIMACS source data."""
import unittest

from witnora_core.python_dimacs_xor_lean_export import (
    checked_python_clauses, default_xor_cases, dimacs_bytes,
    emit_python_dimacs_lean,
)
from witnora_core.xor import canonical_xor_cnf_clauses


class XorDimacsSourceTests(unittest.TestCase):
    def test_actual_python_encoder_set_exact(self):
        for _, raw, rhs in default_xor_cases():
            equation, ordered = checked_python_clauses(raw, rhs)
            self.assertEqual(set(ordered), canonical_xor_cnf_clauses(raw, rhs))
            self.assertEqual(len(ordered), len(set(ordered)))
            self.assertEqual(equation.rhs, rhs)

    def test_source_bytes_recover_all_clauses(self):
        for _, raw, rhs in default_xor_cases():
            equation, clauses, source = dimacs_bytes(raw, rhs)
            text = source.decode("ascii")
            lines = text.splitlines()
            self.assertEqual(lines[0],
                             f"p cnf {max(equation.variables, default=0)} {len(clauses)}")
            parsed = tuple(tuple(map(int, line.split()[:-1]))
                           for line in lines[1:])
            self.assertEqual(parsed, clauses)
            self.assertTrue(all(line.split()[-1] == "0" for line in lines[1:]))

    def test_deterministic_source_proofs(self):
        source = emit_python_dimacs_lean()
        self.assertEqual(source, emit_python_dimacs_lean())
        for name, _, _ in default_xor_cases():
            self.assertIn(f"{name}DocumentPasses", source)
            self.assertIn(f"{name}ExactModelEquivalence", source)
            self.assertIn(f"{name}DocumentAlteredRejects", source)
        self.assertNotIn("native_decide", source)


if __name__ == "__main__":
    unittest.main()
