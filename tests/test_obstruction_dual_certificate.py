import tempfile
import unittest
from pathlib import Path

from witnora_core.obstruction_dual import (
    G0_G6_GRAMMARS,
    G7_GRAMMAR,
    MISSING_OPERATOR_RECOMMENDED,
    NO_CERTIFIED_COLLAPSE_WITH_OBSTRUCTION,
    OBSTRUCTION_DUAL_CERTIFICATE_FAILED,
    OBSTRUCTION_DUAL_CERTIFICATE_VERIFIED,
    build_obstruction_dual_certificate,
    check_obstruction_dual_certificate,
    missing_operator_recommendations,
    obstruction_to_operator_queue,
    run_obstruction_dual_lab,
    target_fixtures,
)


class ObstructionDualCertificateTest(unittest.TestCase):
    def _fixture(self, family="near-affine"):
        return target_fixtures([family])[0]

    def _certificate(self, family="near-affine"):
        fixture = self._fixture(family)
        return fixture, build_obstruction_dual_certificate(fixture).to_dict()

    def test_obstruction_dual_cert_schema(self):
        fixture, cert = self._certificate()
        self.assertEqual(cert["type"], "OBSTRUCTION_DUAL_CERTIFICATE")
        self.assertEqual(cert["grammar"], G7_GRAMMAR)
        self.assertEqual(cert["formula_hash"], fixture["formula"].formula_hash)
        self.assertEqual(cert["checker_status"], OBSTRUCTION_DUAL_CERTIFICATE_VERIFIED)
        self.assertIn("result_per_grammar", cert)
        self.assertIn("obstruction_fingerprints", cert)
        self.assertIn("recommended_next_operator", cert)
        print("OBSTRUCTION_DUAL_CERT_SCHEMA_PASS")

    def test_g0_g6_attempt_trace(self):
        _, cert = self._certificate("near-cardinality")
        self.assertEqual(cert["grammars_attempted"], G0_G6_GRAMMARS)
        self.assertEqual(len(cert["result_per_grammar"]), len(G0_G6_GRAMMARS))
        for attempt, grammar in zip(cert["result_per_grammar"], G0_G6_GRAMMARS):
            self.assertEqual(attempt["grammar"], grammar)
            self.assertEqual(attempt["status"], NO_CERTIFIED_COLLAPSE_WITH_OBSTRUCTION)
            self.assertTrue(attempt["evidence"]["not_a_lower_bound"])
            self.assertTrue(attempt["evidence"]["not_a_satisfiability_claim"])
        print("G0_G6_ATTEMPT_TRACE_PASS")

    def test_obstruction_fingerprint_evidence(self):
        _, cert = self._certificate("graph-separator")
        fingerprint = cert["obstruction_fingerprints"][0]
        self.assertEqual(fingerprint["fingerprint_type"], "GRAPH_SEPARATOR_OBSTRUCTION")
        self.assertTrue(fingerprint["features_used"])
        self.assertTrue(fingerprint["evidence"])
        self.assertIn("formula_hash", cert["feature_evidence"])
        print("OBSTRUCTION_FINGERPRINT_EVIDENCE_PASS")

    def test_obstruction_dual_checker(self):
        fixture, cert = self._certificate("proof-motif-near-miss")
        result = check_obstruction_dual_certificate(fixture["formula"], cert)
        self.assertEqual(result["checker_status"], OBSTRUCTION_DUAL_CERTIFICATE_VERIFIED)
        tampered = dict(cert)
        tampered["formula_hash"] = "bad"
        failed = check_obstruction_dual_certificate(fixture["formula"], tampered)
        self.assertEqual(failed["checker_status"], OBSTRUCTION_DUAL_CERTIFICATE_FAILED)
        print("OBSTRUCTION_DUAL_CHECKER_PASS")

    def test_missing_operator_recommendation(self):
        certs = [self._certificate("near-affine")[1], self._certificate("near-cardinality")[1]]
        recommendations = missing_operator_recommendations(certs)
        operators = {row["recommended_operator"] for row in recommendations}
        self.assertIn("ROBUST_AFFINE_COMPLETION_OR_REJECTION", operators)
        self.assertIn("CARDINALITY_COMPLETION_OR_PB_CERTIFICATE", operators)
        queue = obstruction_to_operator_queue(certs)
        self.assertEqual(queue[0]["promotion_status"], "PROOF_OBLIGATION_BEFORE_PROTOTYPE")
        self.assertNotEqual(queue[0]["promotion_status"], MISSING_OPERATOR_RECOMMENDED)
        print("MISSING_OPERATOR_RECOMMENDATION_PASS")

    def test_no_fake_sat_unsat_claim(self):
        _, cert = self._certificate("mixed")
        for attempt in cert["result_per_grammar"]:
            self.assertNotEqual(attempt["status"], "SAT")
            self.assertNotEqual(attempt["status"], "UNSAT")
            self.assertNotEqual(attempt["public_category"], "SAT")
            self.assertNotEqual(attempt["public_category"], "UNSAT")
        tampered = dict(cert)
        tampered["result_per_grammar"] = [dict(cert["result_per_grammar"][0], status="SAT")]
        result = check_obstruction_dual_certificate(self._fixture("mixed")["formula"], tampered)
        self.assertEqual(result["checker_status"], OBSTRUCTION_DUAL_CERTIFICATE_FAILED)
        print("NO_FAKE_SAT_UNSAT_CLAIM_PASS")

    def test_no_fake_hardness_claim(self):
        _, cert = self._certificate("near-affine")
        boundary = cert["claim_boundary"].lower()
        self.assertIn("no hardness claim", boundary)
        self.assertNotIn("is hard", boundary)
        self.assertNotIn("hard for all algorithms", boundary)
        print("NO_FAKE_HARDNESS_CLAIM_PASS")

    def test_no_lower_bound_overclaim(self):
        _, cert = self._certificate("near-cardinality")
        self.assertEqual(cert["failed_route_evidence"]["scope"], "bounded diagnostic evidence, not lower-bound proof")
        self.assertIn("no lower-bound claim", cert["claim_boundary"])
        for attempt in cert["result_per_grammar"]:
            self.assertTrue(attempt["evidence"]["not_a_lower_bound"])
        print("NO_LOWER_BOUND_OVERCLAIM_PASS")

    def test_no_pnp_claim(self):
        _, cert = self._certificate("graph-separator")
        text = str(cert)
        self.assertIn("no P vs NP progress claim", cert["claim_boundary"])
        self.assertNotIn("proves P vs NP", text)
        self.assertNotIn("P vs NP progress", text.replace("no P vs NP progress", ""))
        print("NO_PNP_CLAIM_PASS")

    def test_no_hard_unknown_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_root = Path(tmp) / "v214"
            result = run_obstruction_dual_lab(
                families=["near-affine", "near-cardinality", "graph-separator"],
                out_root=out_root,
                strict=True,
                zip_path=None,
            )
            for cert in result["obstruction_dual_certificates"]:
                for attempt in cert["result_per_grammar"]:
                    self.assertNotEqual(attempt["status"], "HARD")
                    self.assertNotEqual(attempt["status"], "UNKNOWN")
                    self.assertNotEqual(attempt["public_category"], "HARD")
                    self.assertNotEqual(attempt["public_category"], "UNKNOWN")
            generated_text = (out_root / "OBSTRUCTION_DUAL_CERTIFICATE_REPORT.md").read_text(encoding="utf-8")
            self.assertNotIn("HARD", generated_text)
            self.assertNotIn("UNKNOWN", generated_text)
        print("NO_HARD_UNKNOWN_STATUS_PASS")


if __name__ == "__main__":
    unittest.main()
