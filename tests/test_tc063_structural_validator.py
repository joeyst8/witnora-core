import unittest

from witnora_core.separator_affine_family_theorem import make_separator_affine_instance
from witnora_core.tc063_theorem_hardening import (
    SAF_MEMBER_REJECTED,
    SAF_MEMBER_VERIFIED,
    validate_saf_membership,
)


class TC063StructuralValidatorTest(unittest.TestCase):
    def test_saf_membership_validator(self):
        instance = make_separator_affine_instance("saf_sat_chain_8")
        validation = validate_saf_membership(instance.formula, c=1, r=2, separator_variables=[1])
        self.assertEqual(validation.validation_status, SAF_MEMBER_VERIFIED)
        self.assertTrue(validation.every_assignment_localized)
        self.assertTrue(validation.every_component_affine_verified)
        self.assertEqual(validation.separator_assignment_count, 2)
        print("SAF_MEMBERSHIP_VALIDATOR_PASS")

    def test_saf_non_member_reject(self):
        instance = make_separator_affine_instance("non_affine_component")
        validation = validate_saf_membership(instance.formula, c=1, r=2, separator_variables=[1])
        self.assertEqual(validation.validation_status, SAF_MEMBER_REJECTED)
        self.assertIn("COMPONENT_NOT_EXACT_AFFINE", validation.invalid_reason)
        print("SAF_NON_MEMBER_REJECT_PASS")


if __name__ == "__main__":
    unittest.main()
