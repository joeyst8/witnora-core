"""Real Lean adversarial checks for the complete source-bound G14 gate.

These tests intentionally tamper with proof construction *after* the production
normalization and per-branch checks have passed. They verify that the final
combined Lean theorem independently rejects the altered evidence.
"""
import unittest
from unittest.mock import patch

from witnora_core import lean_g14_gate
from witnora_core.separator_affine_family_theorem import (
    build_separator_affine_certificate,
    make_separator_affine_instance,
)


class RealLeanG14AdversarialTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        instance = make_separator_affine_instance("saf_unsat_cover_2")
        cls.formula = instance.formula
        cls.certificate = build_separator_affine_certificate(instance)
        cls.raw = cls.formula.to_clause_lists()
        cls.tokens = [value for row in cls.raw for value in (*row, 0)]
        cls.source = cls.formula.canonical_dimacs()

    def verify(self):
        return lean_g14_gate.verify_g14_unsat_cover_with_lean(
            self.formula,
            self.certificate,
            raw_clauses=self.raw,
            source_tokens=self.tokens,
            source_spellings=list(map(str, self.tokens)),
            source_text=self.source,
            timeout_seconds=240,
        )

    def test_combined_kernel_rejects_source_modified_after_normalization(self):
        actual = lean_g14_gate._check_complete_g14_with_lean

        def altered_source(*args, **kwargs):
            values = list(args)
            values[3] = values[3].replace("p cnf", "p cna", 1)
            self.assertNotEqual(values[3], self.source)
            return actual(*values, **kwargs)

        with patch.object(lean_g14_gate, "_check_complete_g14_with_lean",
                          side_effect=altered_source):
            result = self.verify()
        self.assertFalse(result["verified"], result)
        self.assertEqual(result["lean_formal_status"], "NOT_LEAN_VERIFIED")
        self.assertIn("Lean rejected complete G14 theorem", result["detail"])

    def test_combined_kernel_rejects_corrupted_g5_rows(self):
        # The standalone G5 verifications still use their real original rows.
        # Only the final combined theorem receives this forged row encoding.
        with patch.object(lean_g14_gate, "_serialize_rows", return_value="[]"):
            result = self.verify()
        self.assertFalse(result["verified"], result)
        self.assertEqual(result["lean_formal_status"], "NOT_LEAN_VERIFIED")
        self.assertIn("Lean rejected complete G14 theorem", result["detail"])


if __name__ == "__main__":
    unittest.main()
