import unittest

from witnora_core.finite_edge_certificate import (
    FINITE,
    FINITE_EDGE_DELTA_CERTIFICATE,
    FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED,
    G1_XOR,
    G2_SYMMETRY_CERTIFIED,
    LOWER_REPLAY_NO_COLLAPSE,
    build_finite_edge_delta_certificate,
)


class FiniteEdgeDeltaCertificateSchemaTest(unittest.TestCase):
    def test_finite_edge_delta_cert_schema(self):
        cert = build_finite_edge_delta_certificate(
            instances=["cycle_4_3color", "cycle_6_3color"],
        ).to_dict()
        self.assertEqual(cert["type"], FINITE_EDGE_DELTA_CERTIFICATE)
        self.assertEqual(cert["lower_grammar"], G1_XOR)
        self.assertEqual(cert["upper_grammar"], G2_SYMMETRY_CERTIFIED)
        self.assertEqual(cert["claim_scope"], FINITE)
        self.assertEqual(cert["evidence_grade"], FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED)
        self.assertIn("certificate_id", cert)
        print("FINITE_EDGE_DELTA_CERT_SCHEMA_PASS")
        print("FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED_PASS")

    def test_finite_edge_delta_instance_record(self):
        cert = build_finite_edge_delta_certificate(instances=["cycle_4_3color"]).to_dict()
        record = cert["instances"][0]
        self.assertEqual(record["instance_id"], "cycle_4_3color")
        self.assertIn("formula_hash", record)
        self.assertEqual(record["lower_result"]["evidence_type"], LOWER_REPLAY_NO_COLLAPSE)
        self.assertIn("upper_result", record)
        self.assertIn("not a lower-bound strictness theorem", record["claim_boundary"])
        print("FINITE_EDGE_DELTA_INSTANCE_RECORD_PASS")


if __name__ == "__main__":
    unittest.main()
