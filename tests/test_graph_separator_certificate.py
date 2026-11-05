import unittest

from witnora_core.graph_separator_lift import (
    G8_GRAPH_SEPARATOR_NATIVE_CERTIFIED,
    GRAPH_SEPARATOR_CERTIFICATE_FAILED,
    GRAPH_SEPARATOR_CERTIFICATE_VERIFIED,
    GRAPH_SEPARATOR_DRAT_NOT_CLAIMED,
    SAT_GRAPH_SEPARATOR_NATIVE_CERTIFIED,
    UNSAT_GRAPH_SEPARATOR_NATIVE_CERTIFIED,
    build_graph_separator_certificate,
    check_graph_separator_certificate,
    make_graph_separator_instance,
)


class GraphSeparatorCertificateTest(unittest.TestCase):
    def test_graph_separator_cert_schema(self):
        instance = make_graph_separator_instance("separator_sat_pair")
        cert = build_graph_separator_certificate(instance).to_dict()
        self.assertEqual(cert["type"], "GRAPH_SEPARATOR_LIFT_CERTIFICATE")
        self.assertEqual(cert["graph_model"], "PRIMAL")
        self.assertEqual(cert["separator_variables"], [1])
        self.assertTrue(cert["components"])
        self.assertTrue(cert["separator_assignments"])
        self.assertEqual(cert["checker_status"], GRAPH_SEPARATOR_CERTIFICATE_VERIFIED)
        self.assertEqual(cert["certification_level"], G8_GRAPH_SEPARATOR_NATIVE_CERTIFIED)
        print("GRAPH_SEPARATOR_CERT_SCHEMA_PASS")

    def test_graph_separator_sat_witness_lift(self):
        instance = make_graph_separator_instance("separator_sat_pair")
        cert = build_graph_separator_certificate(instance).to_dict()
        self.assertEqual(cert["public_category"], SAT_GRAPH_SEPARATOR_NATIVE_CERTIFIED)
        self.assertEqual(cert["sat_lift"]["combined_assignment_verified_against_original_cnf"], True)
        check = check_graph_separator_certificate(instance.formula, cert)
        self.assertEqual(check["checker_status"], GRAPH_SEPARATOR_CERTIFICATE_VERIFIED)
        print("GRAPH_SEPARATOR_SAT_WITNESS_LIFT_PASS")

    def test_graph_separator_unsat_cover(self):
        instance = make_graph_separator_instance("separator_unsat_cover")
        cert = build_graph_separator_certificate(instance).to_dict()
        self.assertEqual(cert["public_category"], UNSAT_GRAPH_SEPARATOR_NATIVE_CERTIFIED)
        self.assertEqual(cert["unsat_cover"]["all_separator_assignments_covered"], True)
        self.assertEqual(set(cert["unsat_cover"]["separator_assignment_ids"]), {"S0", "S1"})
        print("GRAPH_SEPARATOR_UNSAT_COVER_PASS")

    def test_graph_separator_no_fake_drat(self):
        instance = make_graph_separator_instance("separator_sat_pair")
        cert = build_graph_separator_certificate(instance).to_dict()
        self.assertEqual(cert["drat_claim"], GRAPH_SEPARATOR_DRAT_NOT_CLAIMED)
        self.assertNotIn("DRAT", cert["public_category"])
        bad = dict(cert)
        bad["drat_claim"] = "UNSAT_DRAT_EXPORTED_VERIFIED"
        result = check_graph_separator_certificate(instance.formula, bad)
        self.assertEqual(result["checker_status"], GRAPH_SEPARATOR_CERTIFICATE_FAILED)
        print("GRAPH_SEPARATOR_NO_FAKE_DRAT_PASS")


if __name__ == "__main__":
    unittest.main()
