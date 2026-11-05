import unittest

from witnora_core.operator_genesis import (
    AFFINE_RESIDUE_CERTIFICATE_FAILED,
    AFFINE_RESIDUE_CERTIFICATE_VERIFIED,
    build_affine_residue_certificate,
    check_affine_residue_certificate,
    make_affine_residue_instance,
)


class AffineResidueCheckerTest(unittest.TestCase):
    def test_affine_residue_cert_checker(self):
        instance = make_affine_residue_instance("mixed_affine_arity_8_unsat")
        cert = build_affine_residue_certificate(instance)
        result = check_affine_residue_certificate(instance.formula, cert)
        self.assertEqual(result["status"], AFFINE_RESIDUE_CERTIFICATE_VERIFIED)
        print("AFFINE_RESIDUE_CERT_CHECKER_PASS")

    def test_affine_residue_cert_tamper_reject(self):
        instance = make_affine_residue_instance("parity_arity_7_unsat")
        cert = build_affine_residue_certificate(instance).to_dict()
        cert["equations"][0]["source_clause_ids"] = cert["equations"][0]["source_clause_ids"][1:]
        result = check_affine_residue_certificate(instance.formula, cert)
        self.assertEqual(result["status"], AFFINE_RESIDUE_CERTIFICATE_FAILED)
        self.assertTrue(any(error.startswith("AFFINE_SOURCE_CLAUSE_IDS_MISMATCH") for error in result["errors"]))
        print("AFFINE_RESIDUE_CERT_TAMPER_REJECT_PASS")

    def test_affine_wrong_parity_reject(self):
        instance = make_affine_residue_instance("parity_arity_7_sat")
        cert = build_affine_residue_certificate(instance).to_dict()
        cert["equations"][0]["parity_bit"] ^= 1
        result = check_affine_residue_certificate(instance.formula, cert)
        self.assertEqual(result["status"], AFFINE_RESIDUE_CERTIFICATE_FAILED)
        self.assertTrue(any(error.startswith("AFFINE_FULL_ENCODING_MISSING") for error in result["errors"]))
        print("AFFINE_WRONG_PARITY_REJECT_PASS")

    def test_gf2_trace_checker(self):
        instance = make_affine_residue_instance("mixed_affine_arity_8_sat")
        cert = build_affine_residue_certificate(instance)
        result = check_affine_residue_certificate(instance.formula, cert)
        self.assertEqual(result["status"], AFFINE_RESIDUE_CERTIFICATE_VERIFIED)
        self.assertEqual(result["gf2_status"], "SAT")
        print("GF2_TRACE_CHECKER_PASS")

    def test_gf2_no_nontrivial_scale_row(self):
        instance = make_affine_residue_instance("parity_arity_7_unsat")
        cert = build_affine_residue_certificate(instance).to_dict()
        cert["row_operations"].append({"operation": "SCALE_ROW_NONTRIVIAL", "row": 0, "factor": 2})
        result = check_affine_residue_certificate(instance.formula, cert)
        self.assertEqual(result["status"], AFFINE_RESIDUE_CERTIFICATE_FAILED)
        self.assertIn("GF2_NONTRIVIAL_SCALE_ROW_FORBIDDEN", result["errors"])
        print("GF2_NO_NONTRIVIAL_SCALE_ROW_PASS")


if __name__ == "__main__":
    unittest.main()
