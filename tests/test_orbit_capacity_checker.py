import unittest

from witnora_core.operator_genesis import (
    ORBIT_CAPACITY_CERTIFICATE_FAILED,
    ORBIT_CAPACITY_CERTIFICATE_VERIFIED,
    build_orbit_capacity_certificate,
    check_orbit_capacity_certificate,
    make_orbit_capacity_instance,
)


class OrbitCapacityCheckerTest(unittest.TestCase):
    def test_orbit_capacity_cert_checker(self):
        instance = make_orbit_capacity_instance("hall_local_5_4")
        cert = build_orbit_capacity_certificate(instance)
        result = check_orbit_capacity_certificate(instance.formula, cert)
        self.assertEqual(result["status"], ORBIT_CAPACITY_CERTIFICATE_VERIFIED)
        print("ORBIT_CAPACITY_CERT_CHECKER_PASS")

    def test_orbit_capacity_cert_tamper_reject(self):
        instance = make_orbit_capacity_instance("hall_local_4_3")
        cert = build_orbit_capacity_certificate(instance).to_dict()
        cert["demand_count"] = 1
        result = check_orbit_capacity_certificate(instance.formula, cert)
        self.assertEqual(result["status"], ORBIT_CAPACITY_CERTIFICATE_FAILED)
        self.assertIn("DEMAND_COUNT_MISMATCH", result["errors"])
        print("ORBIT_CAPACITY_CERT_TAMPER_REJECT_PASS")

    def test_orbit_capacity_incomplete_alo_reject(self):
        instance = make_orbit_capacity_instance("hall_local_4_3")
        cert = build_orbit_capacity_certificate(instance).to_dict()
        cert["alo_clause_ids_by_item"].pop("a")
        result = check_orbit_capacity_certificate(instance.formula, cert)
        self.assertEqual(result["status"], ORBIT_CAPACITY_CERTIFICATE_FAILED)
        self.assertIn("ALO_CLAUSE_ID_MISMATCH:a", result["errors"])
        print("ORBIT_CAPACITY_INCOMPLETE_ALO_REJECT_PASS")

    def test_orbit_capacity_incomplete_amo_reject(self):
        instance = make_orbit_capacity_instance("incomplete_capacity_structure_reject")
        cert = build_orbit_capacity_certificate(instance)
        result = check_orbit_capacity_certificate(instance.formula, cert)
        self.assertEqual(result["status"], ORBIT_CAPACITY_CERTIFICATE_FAILED)
        self.assertTrue(any(error.startswith("CAPACITY_CLAUSE_MISSING") for error in result["errors"]))
        print("ORBIT_CAPACITY_INCOMPLETE_AMO_REJECT_PASS")

    def test_orbit_capacity_balanced_no_contradiction(self):
        instance = make_orbit_capacity_instance("capacity_balanced_4_4_no_contradiction")
        cert = build_orbit_capacity_certificate(instance)
        self.assertEqual(cert.public_category, "NO_COLLAPSE_FOUND")
        self.assertEqual(cert.checker_status, ORBIT_CAPACITY_CERTIFICATE_FAILED)
        print("ORBIT_CAPACITY_BALANCED_NO_CONTRADICTION_PASS")

    def test_orbit_compression_expand_verify(self):
        instance = make_orbit_capacity_instance("hall_local_4_3")
        cert = build_orbit_capacity_certificate(instance)
        self.assertTrue(cert.orbit_compression_used)
        self.assertTrue(cert.orbit_expanded_and_verified)
        print("ORBIT_COMPRESSION_EXPAND_VERIFY_PASS")

    def test_orbit_compression_no_trust_without_expansion(self):
        instance = make_orbit_capacity_instance("hall_local_4_3")
        cert = build_orbit_capacity_certificate(instance).to_dict()
        cert["orbit_expanded_and_verified"] = False
        result = check_orbit_capacity_certificate(instance.formula, cert)
        self.assertEqual(result["status"], ORBIT_CAPACITY_CERTIFICATE_FAILED)
        self.assertIn("ORBIT_COMPRESSION_NOT_EXPANDED", result["errors"])
        print("ORBIT_COMPRESSION_NO_TRUST_WITHOUT_EXPANSION_PASS")


if __name__ == "__main__":
    unittest.main()
