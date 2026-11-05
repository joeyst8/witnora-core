import unittest
from pathlib import Path

from witnora_core.separator_affine_family_theorem import (
    G14_GRAMMAR,
    SEPARATOR_AFFINE_FAMILY_RECOGNIZED,
    recognize_separator_affine_family,
    make_separator_affine_instance,
)
from witnora_core.theorem_candidates import initial_theorem_candidates


class SeparatorAffineFamilyTheoremTest(unittest.TestCase):
    def test_recognition_algorithm(self):
        instance = make_separator_affine_instance("saf_sat_chain_8")
        recognition = recognize_separator_affine_family(instance.formula, c=1, r=2)
        self.assertEqual(recognition["status"], SEPARATOR_AFFINE_FAMILY_RECOGNIZED)
        self.assertEqual(recognition["separator_variables"], [1])
        self.assertIn("O(n^c * 2^c * poly(n))", recognition["complexity"])

    def test_theorem_document_nonclaims(self):
        text = Path("theory/BOUNDED_SEPARATOR_AFFINE_COLLAPSE_THEOREM.md").read_text(encoding="utf-8")
        self.assertIn("Formal Definition SAF(c,r)", text)
        self.assertIn("SAT: there exists one separator assignment", text)
        self.assertIn("UNSAT: every separator assignment", text)
        self.assertIn("polynomial for fixed `c`", text)
        self.assertIn("No P vs NP progress", text)

    def test_tc063_theorem_registry(self):
        candidates = {candidate.id: candidate for candidate in initial_theorem_candidates()}
        self.assertIn("TC-063", candidates)
        tc063 = candidates["TC-063"]
        self.assertEqual(tc063.name, "Bounded Separator-Affine Collapse Theorem")
        self.assertEqual(tc063.status, "RESTRICTED_THEOREM_WITH_PROOF_OBLIGATIONS")
        joined = "\n".join(tc063.forbidden_interpretations)
        self.assertIn("Does not claim P vs NP progress", joined)
        self.assertIn("Does not claim all SAT", joined)
        self.assertIn("Does not claim hierarchy completeness", joined)
        print("TC063_THEOREM_REGISTRY_PASS")

    def test_g14_name_present(self):
        self.assertEqual(G14_GRAMMAR, "G14_BOUNDED_SEPARATOR_AFFINE_FAMILY_THEOREM")


if __name__ == "__main__":
    unittest.main()
