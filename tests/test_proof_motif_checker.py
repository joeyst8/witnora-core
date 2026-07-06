import copy
import unittest

from witnora_core.operator_genesis import (
    PROOF_MOTIF_CERTIFICATE_FAILED,
    PROOF_MOTIF_CERTIFICATE_VERIFIED,
    _proof_motif_template,
    _verify_template_proof,
    build_proof_motif_certificate,
    check_proof_motif_certificate,
    make_proof_motif_instance,
)


class ProofMotifCheckerTest(unittest.TestCase):
    def test_resolution_and_unit_steps(self):
        resolution_ok, resolution_errors, _ = _verify_template_proof(_proof_motif_template("RESOLUTION_TEMPLATE"))
        unit_ok, unit_errors, _ = _verify_template_proof(_proof_motif_template("UNIT_PROPAGATION_TEMPLATE"))
        self.assertTrue(resolution_ok, resolution_errors)
        self.assertTrue(unit_ok, unit_errors)
        print("PROOF_MOTIF_RESOLUTION_STEP_CHECK_PASS")
        print("PROOF_MOTIF_UNIT_PROP_STEP_CHECK_PASS")

    def test_bad_reuse_rejected(self):
        instance = make_proof_motif_instance("motif_ladder_4")
        cert = build_proof_motif_certificate(instance).to_dict()
        cert["reuse_sites"][0]["source_clause_ids"][0] = 999999
        result = check_proof_motif_certificate(instance.formula, cert)
        self.assertEqual(result["status"], PROOF_MOTIF_CERTIFICATE_FAILED)
        print("PROOF_MOTIF_BAD_REUSE_REJECT_PASS")

    def test_bad_substitution_rejected(self):
        instance = make_proof_motif_instance("motif_ladder_4")
        cert = build_proof_motif_certificate(instance).to_dict()
        cert["reuse_sites"][0]["substitution_map"] = {"1": 1, "2": 1}
        result = check_proof_motif_certificate(instance.formula, cert)
        self.assertEqual(result["status"], PROOF_MOTIF_CERTIFICATE_FAILED)
        print("PROOF_MOTIF_BAD_SUBSTITUTION_REJECT_PASS")

    def test_tamper_rejected(self):
        instance = make_proof_motif_instance("motif_ladder_4")
        cert = build_proof_motif_certificate(instance).to_dict()
        cert["formula_hash"] = "0" * 64
        result = check_proof_motif_certificate(instance.formula, cert)
        self.assertEqual(result["status"], PROOF_MOTIF_CERTIFICATE_FAILED)
        print("PROOF_MOTIF_TAMPER_REJECT_PASS")

    def test_valid_checker_passes(self):
        instance = make_proof_motif_instance("motif_ladder_4")
        cert = build_proof_motif_certificate(instance)
        result = check_proof_motif_certificate(instance.formula, cert)
        self.assertEqual(result["status"], PROOF_MOTIF_CERTIFICATE_VERIFIED)


if __name__ == "__main__":
    unittest.main()
