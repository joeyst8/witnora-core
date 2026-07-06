import unittest

from witnora_core.strictness_proof import (
    WIDTH_EXCEEDS_CAP_VERIFIED,
    WIDTH_OBSTRUCTION_VERIFIED,
    build_width_obstruction_certificate,
    strictness_witness_formula,
)


class StrictnessProofWidthTest(unittest.TestCase):
    def test_width_obstruction_cert_schema(self):
        _, formula, _ = strictness_witness_formula("tseitin_10")
        cert = build_width_obstruction_certificate(formula, instance_id="tseitin_10", cap_c=4)
        data = cert.to_dict()
        self.assertEqual(data["graph_type"], "PRIMAL")
        self.assertEqual(data["width_parameter"], "INDUCED_WIDTH")
        self.assertEqual(data["cap_c"], 4)
        self.assertIn("formula_hash", data)
        print("WIDTH_OBSTRUCTION_CERT_SCHEMA_PASS")

    def test_exact_width_audit_and_exceeds_cap(self):
        _, formula, _ = strictness_witness_formula("tseitin_10")
        cert = build_width_obstruction_certificate(formula, instance_id="tseitin_10", cap_c=4)
        self.assertEqual(cert.checker_status, WIDTH_OBSTRUCTION_VERIFIED)
        self.assertEqual(cert.obstruction_status, WIDTH_EXCEEDS_CAP_VERIFIED)
        self.assertGreater(cert.certified_lower_bound or 0, cert.cap_c)
        print("EXACT_WIDTH_AUDIT_PASS")
        print("WIDTH_EXCEEDS_CAP_VERIFIED_PASS")
        print("RESTRICTED_G0_WIDTH_ROUTE_REJECTED_PASS")


if __name__ == "__main__":
    unittest.main()

