import unittest

from witnora_core.collapse_theory import (
    NO_COLLAPSE_FOUND,
    PIGEONHOLE_CERTIFICATE_FAILED,
    PIGEONHOLE_CERTIFICATE_VERIFIED,
    PIGEONHOLE_DRAT_NOT_CLAIMED,
    PIGEONHOLE_NATIVE_COUNTING_UNSAT,
    UNSAT_PIGEONHOLE_NATIVE_CERTIFIED,
    TheoryInstance,
    _pigeonhole_formula,
    build_pigeonhole_counting_certificate,
    check_pigeonhole_certificate,
)


class PigeonholeNativeCertificateTest(unittest.TestCase):
    def _instance(self, n: int, m: int) -> TheoryInstance:
        return TheoryInstance(f"php_{n}_{m}", "pigeonhole", _pigeonhole_formula(n, m), "test")

    def test_pigeonhole_native_counting_unsat(self):
        cert = build_pigeonhole_counting_certificate(self._instance(3, 2))
        self.assertEqual(cert.status, PIGEONHOLE_NATIVE_COUNTING_UNSAT)
        self.assertEqual(cert.public_category, UNSAT_PIGEONHOLE_NATIVE_CERTIFIED)
        print("PIGEONHOLE_NATIVE_COUNTING_UNSAT_PASS")

    def test_pigeonhole_cert_checker(self):
        instance = self._instance(4, 3)
        cert = build_pigeonhole_counting_certificate(instance)
        result = check_pigeonhole_certificate(instance.formula, cert)
        self.assertEqual(result["status"], PIGEONHOLE_CERTIFICATE_VERIFIED)
        print("PIGEONHOLE_CERT_CHECKER_PASS")

    def test_pigeonhole_cert_tamper_reject(self):
        instance = self._instance(4, 3)
        cert = build_pigeonhole_counting_certificate(instance).to_dict()
        cert["assignment_variable_grid"][0]["variable"] = 999
        result = check_pigeonhole_certificate(instance.formula, cert)
        self.assertEqual(result["status"], PIGEONHOLE_CERTIFICATE_FAILED)
        self.assertIn("ASSIGNMENT_VARIABLE_GRID_MISMATCH", result["errors"])
        print("PIGEONHOLE_CERT_TAMPER_REJECT_PASS")

    def test_pigeonhole_php_rows(self):
        for n, m, marker in [(3, 2, "PIGEONHOLE_PHP_3_2_PASS"), (4, 3, "PIGEONHOLE_PHP_4_3_PASS"), (5, 4, "PIGEONHOLE_PHP_5_4_PASS")]:
            cert = build_pigeonhole_counting_certificate(self._instance(n, m))
            self.assertEqual(cert.checker_status, PIGEONHOLE_CERTIFICATE_VERIFIED)
            self.assertEqual(cert.public_category, UNSAT_PIGEONHOLE_NATIVE_CERTIFIED)
            print(marker)

    def test_pigeonhole_no_fake_drat_claim(self):
        cert = build_pigeonhole_counting_certificate(self._instance(3, 2))
        self.assertEqual(cert.drat_claim, PIGEONHOLE_DRAT_NOT_CLAIMED)
        bad = cert.to_dict()
        bad["drat_claim"] = "UNSAT_DRAT_EXPORTED_VERIFIED"
        result = check_pigeonhole_certificate(self._instance(3, 2).formula, bad)
        self.assertEqual(result["status"], PIGEONHOLE_CERTIFICATE_FAILED)
        self.assertIn("FAKE_DRAT_CLAIM", result["errors"])
        print("PIGEONHOLE_NO_FAKE_DRAT_CLAIM_PASS")

    def test_n_le_m_certificate_fails(self):
        cert = build_pigeonhole_counting_certificate(self._instance(2, 2))
        self.assertEqual(cert.public_category, NO_COLLAPSE_FOUND)
        self.assertEqual(cert.status, PIGEONHOLE_CERTIFICATE_FAILED)


if __name__ == "__main__":
    unittest.main()
