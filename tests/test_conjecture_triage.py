"""Ensure known identities and unproved Lean queue cannot be misreported."""
import unittest

from witnora_core.conjecture_triage import (
    normalize_expression, identity_key, known_identity_keys, triage,
)


class ConjectureTriageTests(unittest.TestCase):
    def test_commutative_normalization_and_known_identity(self):
        self.assertEqual(normalize_expression("(tau+alpha)"), "(alpha+tau)")
        self.assertEqual(identity_key("n = (tau+alpha)"),
                         identity_key("n = (alpha+tau)"))
        self.assertIn(identity_key("n = (alpha+tau)"), known_identity_keys())

    def test_fail_closed_queue(self):
        result = triage(adversarial_per_seed=12)
        self.assertFalse(result["known_identity_catalog_complete"])
        self.assertFalse(result["theorem_proven"])
        for item in result["lean_review_queue"]:
            self.assertEqual(item["status"], "PENDING_FORMALIZATION")
            self.assertFalse(item["lean_verified"])
            self.assertFalse(item["novelty_verified"])


if __name__ == "__main__":
    unittest.main()
