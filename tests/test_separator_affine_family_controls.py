import unittest

from witnora_core.separator_affine_family_theorem import (
    SEPARATOR_AFFINE_CERTIFICATE_FAILED,
    build_separator_affine_certificate,
    check_separator_affine_certificate,
    make_separator_affine_instance,
)


class SeparatorAffineFamilyControlsTest(unittest.TestCase):
    def _rejects(self, instance_id, expected_fragment=None):
        instance = make_separator_affine_instance(instance_id)
        cert = build_separator_affine_certificate(instance)
        check = check_separator_affine_certificate(instance.formula, cert)
        self.assertEqual(check["checker_status"], SEPARATOR_AFFINE_CERTIFICATE_FAILED)
        if expected_fragment:
            self.assertTrue(
                any(expected_fragment in error for error in check["errors"]),
                msg=f"{expected_fragment} not found in {check['errors']}",
            )
        return check

    def test_invalid_large_separator_reject(self):
        self._rejects("invalid_large_separator", "SEPARATOR_SIZE_OVER_BOUND")
        print("SEPARATOR_AFFINE_INVALID_LARGE_SEPARATOR_REJECT_PASS")

    def test_non_affine_component_reject(self):
        self._rejects("non_affine_component", "COMPONENT_NOT_EXACT_AFFINE")
        print("SEPARATOR_AFFINE_NON_AFFINE_COMPONENT_REJECT_PASS")

    def test_invalid_cross_clause_reject(self):
        check = self._rejects("invalid_cross_clause")
        self.assertTrue(
            any(
                "RESIDUAL_CLAUSE_SPANS_COMPONENTS" in error
                or "COMPONENT_NOT_EXACT_AFFINE" in error
                for error in check["errors"]
            ),
            msg=f"invalid cross clause was rejected for an unexpected reason: {check['errors']}",
        )
        print("SEPARATOR_AFFINE_INVALID_CROSS_CLAUSE_REJECT_PASS")

    def test_incomplete_unsat_cover_reject(self):
        self._rejects("incomplete_unsat_cover", "UNSAT_COVER")
        print("SEPARATOR_AFFINE_INCOMPLETE_UNSAT_COVER_REJECT_PASS")

    def test_bad_component_cert_reject(self):
        self._rejects("bad_component_affine_certificate", "COMPONENT_AFFINE_CERT_FAILED")
        print("SEPARATOR_AFFINE_BAD_COMPONENT_CERT_REJECT_PASS")

    def test_bad_sat_witness_reject(self):
        self._rejects("bad_sat_witness", "SAT_WITNESS_DOES_NOT_SATISFY_ORIGINAL_CNF")
        print("SEPARATOR_AFFINE_BAD_SAT_WITNESS_REJECT_PASS")

    def test_tamper_reject(self):
        self._rejects("tamper_separator_assignment", "SEPARATOR_ASSIGNMENT_TAMPER")
        self._rejects("tamper_certificate", "SEPARATOR_ASSIGNMENT_TAMPER")
        print("SEPARATOR_AFFINE_TAMPER_REJECT_PASS")

    def test_fake_drat_reject(self):
        self._rejects("fake_drat_claim", "FAKE_DRAT_CLAIM")
        print("SEPARATOR_AFFINE_NO_FAKE_DRAT_PASS")

    def test_fake_pnp_reject(self):
        self._rejects("fake_pnp_claim", "FORBIDDEN_CLAIM:P_VS_NP_PROGRESS")
        print("SEPARATOR_AFFINE_NO_PNP_CLAIM_PASS")

    def test_fake_completeness_reject(self):
        self._rejects("fake_completeness_claim", "FORBIDDEN_CLAIM:HIERARCHY_COMPLETENESS")
        print("SEPARATOR_AFFINE_NO_COMPLETENESS_CLAIM_PASS")

    def test_hard_unknown_status_reject(self):
        self._rejects("hard_unknown_status_reject", "FORBIDDEN_STATUS:UNKNOWN")
        print("SEPARATOR_AFFINE_NO_HARD_UNKNOWN_STATUS_PASS")


if __name__ == "__main__":
    unittest.main()
