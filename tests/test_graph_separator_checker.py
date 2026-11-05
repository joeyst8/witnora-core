import unittest

from witnora_core.graph_separator_lift import (
    GRAPH_SEPARATOR_CERTIFICATE_FAILED,
    GRAPH_SEPARATOR_CERTIFICATE_VERIFIED,
    build_graph_separator_certificate,
    check_graph_separator_certificate,
    make_graph_separator_instance,
)


class GraphSeparatorCheckerTest(unittest.TestCase):
    def test_graph_separator_checker(self):
        instance = make_graph_separator_instance("separator_sat_pair")
        cert = build_graph_separator_certificate(instance).to_dict()
        result = check_graph_separator_certificate(instance.formula, cert)
        self.assertEqual(result["checker_status"], GRAPH_SEPARATOR_CERTIFICATE_VERIFIED)
        self.assertEqual(result["separator_variables"], [1])
        self.assertEqual(result["component_count"], 2)
        print("GRAPH_SEPARATOR_CHECKER_PASS")

    def test_graph_separator_tamper_reject(self):
        instance = make_graph_separator_instance("separator_sat_pair")
        cert = build_graph_separator_certificate(instance).to_dict()
        cert["formula_hash"] = "bad"
        result = check_graph_separator_certificate(instance.formula, cert)
        self.assertEqual(result["checker_status"], GRAPH_SEPARATOR_CERTIFICATE_FAILED)
        self.assertIn("FORMULA_HASH_MISMATCH", result["errors"])
        print("GRAPH_SEPARATOR_TAMPER_REJECT_PASS")

    def test_graph_separator_incomplete_cover_reject(self):
        instance = make_graph_separator_instance("separator_unsat_cover")
        cert = build_graph_separator_certificate(instance).to_dict()
        cert["unsat_cover"]["blocked_by_component"].pop("S1")
        result = check_graph_separator_certificate(instance.formula, cert)
        self.assertEqual(result["checker_status"], GRAPH_SEPARATOR_CERTIFICATE_FAILED)
        self.assertIn("UNSAT_COVER_INCOMPLETE", result["errors"])
        print("GRAPH_SEPARATOR_INCOMPLETE_COVER_REJECT_PASS")

    def test_graph_separator_bad_component_cert_reject(self):
        instance = make_graph_separator_instance("separator_sat_pair")
        cert = build_graph_separator_certificate(instance).to_dict()
        cert["component_results"][0]["component_witness"] = {"2": False, "3": False}
        result = check_graph_separator_certificate(instance.formula, cert)
        self.assertEqual(result["checker_status"], GRAPH_SEPARATOR_CERTIFICATE_FAILED)
        self.assertTrue(any("COMPONENT_WITNESS_INVALID" in error for error in result["errors"]))
        print("GRAPH_SEPARATOR_BAD_COMPONENT_CERT_REJECT_PASS")


if __name__ == "__main__":
    unittest.main()
