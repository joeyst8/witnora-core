"""Direct TC-063 attack: distinguish family membership from cert soundness.

These are empirical native-validator probes, not proofs of completeness.
"""
import unittest

from witnora_core.separator_affine_family_theorem import make_separator_affine_instance
from witnora_core.tc063_theorem_hardening import (
    SAF_MEMBER_REJECTED,
    SAF_MEMBER_VERIFIED,
    validate_saf_membership,
)


class TC063DirectAttack(unittest.TestCase):
    def test_supported_unsat_family_member(self):
        instance = make_separator_affine_instance("saf_unsat_cover_2")
        record = validate_saf_membership(
            instance.formula, c=1, r=2, separator_variables=[1])
        self.assertEqual(record.validation_status, SAF_MEMBER_VERIFIED)
        self.assertTrue(record.every_component_affine_verified)
        self.assertEqual(record.separator_assignment_count, 2)

    def test_automatic_separator_recognition_on_supported_member(self):
        instance = make_separator_affine_instance("saf_unsat_cover_2")
        record = validate_saf_membership(instance.formula, c=1, r=2)
        self.assertEqual(record.validation_status, SAF_MEMBER_VERIFIED,
                         record.invalid_reason)
        self.assertEqual(record.separator_size, 1)

    def test_non_affine_residual_is_rejected(self):
        instance = make_separator_affine_instance("non_affine_component")
        record = validate_saf_membership(
            instance.formula, c=1, r=2, separator_variables=[1])
        self.assertEqual(record.validation_status, SAF_MEMBER_REJECTED)
        self.assertIn("COMPONENT_NOT_EXACT_AFFINE", record.invalid_reason)

    def test_valid_structure_over_fixed_separator_bound_rejected(self):
        instance = make_separator_affine_instance("saf_unsat_cover_2")
        record = validate_saf_membership(
            instance.formula, c=0, r=2, separator_variables=[1])
        self.assertEqual(record.validation_status, SAF_MEMBER_REJECTED)
        self.assertIn("SEPARATOR_SIZE_OVER_BOUND", record.invalid_reason)


if __name__ == "__main__":
    unittest.main()
