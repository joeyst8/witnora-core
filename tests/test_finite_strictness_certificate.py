import unittest

from witnora_core.finite_strictness_certificate import (
    FINITE,
    FINITE_STRICTNESS_CERTIFICATE,
    FINITE_STRICTNESS_CERTIFIED,
    G0_WIDTH_C,
    G1_XOR_FOR_STRICTNESS,
    build_finite_strictness_certificate,
)


class FiniteStrictnessCertificateSchemaTest(unittest.TestCase):
    def test_finite_strictness_cert_schema(self):
        cert = build_finite_strictness_certificate(
            instances=["tseitin_10", "xor_chain_unsat_n5"],
            cap_c=4,
        ).to_dict()
        self.assertEqual(cert["type"], FINITE_STRICTNESS_CERTIFICATE)
        self.assertEqual(cert["lower_grammar"], G0_WIDTH_C)
        self.assertEqual(cert["upper_grammar"], G1_XOR_FOR_STRICTNESS)
        self.assertEqual(cert["claim_scope"], FINITE)
        self.assertEqual(cert["strictness_status"], FINITE_STRICTNESS_CERTIFIED)
        self.assertIn("certificate_id", cert)
        print("FINITE_STRICTNESS_CERT_SCHEMA_PASS")

    def test_finite_strictness_instance_record(self):
        cert = build_finite_strictness_certificate(
            instances=["tseitin_10"],
            cap_c=4,
        ).to_dict()
        record = cert["instances"][0]
        self.assertEqual(record["instance_id"], "tseitin_10")
        self.assertIn("formula_hash", record)
        self.assertIn("lower_result", record)
        self.assertIn("upper_result", record)
        self.assertIn("not a family theorem", record["claim_boundary"])
        print("FINITE_STRICTNESS_INSTANCE_RECORD_PASS")


if __name__ == "__main__":
    unittest.main()
