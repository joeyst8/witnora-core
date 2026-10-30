"""Syntactic implication, no false proof promotion."""
import unittest

from witnora_core.symbolic_implication import (
    bound_path, derive_equality, triage_with_implications,
)


class SymbolicImplicationTests(unittest.TestCase):
    def test_derive_known_consequence(self):
        result = derive_equality("(alpha+tau) = max(n,alpha)")
        self.assertEqual(result["classification"],
                         "DERIVABLE_RELATIVE_TO_LISTED_AXIOMS")
        self.assertEqual(result["left_normal_form"], "n")
        self.assertEqual(result["right_normal_form"], "n")
        self.assertIn("alpha<=n", result["axiom_references"])
        self.assertFalse(result["lean_verified"])

    def test_reject_unsupported_relation(self):
        result = derive_equality("chi = max(chi,nu)")
        self.assertEqual(result["classification"], "UNRESOLVED_BY_THIS_RULE_SET")
        self.assertIsNone(bound_path("nu", "chi"))

    def test_fail_closed_queue(self):
        report = triage_with_implications()
        self.assertFalse(report["axioms_formally_verified_in_this_experiment"])
        self.assertFalse(report["theorem_proven"])
        self.assertGreaterEqual(len(report["derived_relative_to_axioms"]), 1)
        for row in report["lean_review_queue"]:
            self.assertFalse(row["lean_verified"])


if __name__ == "__main__":
    unittest.main()
