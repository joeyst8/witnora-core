import copy
import unittest

from witnora_core.finite_strictness_certificate import (
    FINITE_STRICTNESS_CERTIFICATE_FAILED,
    FINITE_STRICTNESS_CERTIFICATE_VERIFIED,
    NOT_INCLUDED_RESOURCE_CAP,
    build_finite_strictness_certificate,
    check_finite_strictness_certificate,
)


class FiniteStrictnessCheckerTest(unittest.TestCase):
    def test_finite_strictness_checker_and_certified(self):
        cert = build_finite_strictness_certificate(
            instances=["tseitin_10", "xor_chain_unsat_n5"],
            cap_c=4,
        ).to_dict()
        result = check_finite_strictness_certificate(cert).to_dict()
        self.assertEqual(result["checker_status"], FINITE_STRICTNESS_CERTIFICATE_VERIFIED)
        self.assertEqual(result["checked_instances"], 2)
        self.assertEqual(result["failed_instances"], [])
        print("FINITE_STRICTNESS_CHECKER_PASS")
        print("FINITE_STRICTNESS_CERTIFIED_PASS")

    def test_finite_strictness_tamper_reject(self):
        cert = build_finite_strictness_certificate(instances=["tseitin_10"], cap_c=4).to_dict()
        tampered = copy.deepcopy(cert)
        tampered["instances"][0]["formula_hash"] = "0" * 64
        result = check_finite_strictness_certificate(tampered).to_dict()
        self.assertEqual(result["checker_status"], FINITE_STRICTNESS_CERTIFICATE_FAILED)
        self.assertTrue(result["failed_instances"])
        print("FINITE_STRICTNESS_TAMPER_REJECT_PASS")

    def test_finite_strictness_resource_exclusion(self):
        cert = build_finite_strictness_certificate(
            instances=["tseitin_10", "tseitin_30"],
            cap_c=4,
        ).to_dict()
        self.assertEqual(len(cert["instances"]), 1)
        self.assertEqual(cert["resource_exclusions"][0]["status"], NOT_INCLUDED_RESOURCE_CAP)
        result = check_finite_strictness_certificate(cert).to_dict()
        self.assertEqual(result["checker_status"], FINITE_STRICTNESS_CERTIFICATE_VERIFIED)
        self.assertTrue(result["warnings"])
        print("FINITE_STRICTNESS_RESOURCE_EXCLUSION_PASS")


if __name__ == "__main__":
    unittest.main()
