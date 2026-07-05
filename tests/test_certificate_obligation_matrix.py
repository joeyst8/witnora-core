import unittest

from witnora_core.operator_genesis import (
    SKETCH_ONLY,
    build_certificate_obligation_matrix,
    build_theorem_candidate_queue,
    extract_fingerprints,
    generate_operator_candidates,
)


class CertificateObligationMatrixTest(unittest.TestCase):
    def _candidates(self):
        fingerprints = extract_fingerprints(["pigeonhole", "parity", "graph-coloring", "clique", "adversarial-mixed"])
        return generate_operator_candidates(fingerprints)

    def test_certificate_obligation_matrix(self):
        candidates = self._candidates()
        matrix = build_certificate_obligation_matrix(candidates)
        candidate_ids = {candidate.candidate_id for candidate in candidates}
        matrix_ids = {obligation.candidate_id for obligation in matrix}
        self.assertTrue(candidate_ids.issubset(matrix_ids))
        for obligation in matrix:
            self.assertEqual(obligation.current_status, SKETCH_ONLY)
            self.assertTrue(obligation.no_fake_claim_guardrails)
        print("CERTIFICATE_OBLIGATION_MATRIX_PASS")

    def test_theorem_candidate_queue(self):
        queue = build_theorem_candidate_queue(self._candidates())
        self.assertGreaterEqual(len(queue), 7)
        for item in queue:
            self.assertIn(item["current_status"], {"CONJECTURE", "SPECULATIVE", "EMPIRICAL_EVIDENCE"})
            self.assertNotEqual(item["current_status"], "THEOREM")
        print("THEOREM_CANDIDATE_QUEUE_PASS")

    def test_generated_theorems_not_theorems(self):
        queue = build_theorem_candidate_queue(self._candidates())
        text = "\n".join(" ".join(item["forbidden_interpretations"]) for item in queue)
        self.assertIn("Not a theorem.", text)
        print("GENERATED_THEOREMS_NOT_THEOREMS_PASS")

    def test_no_hallucinated_certificate(self):
        matrix = build_certificate_obligation_matrix(self._candidates())
        for obligation in matrix:
            self.assertIn("independent checker", obligation.missing_pieces)
            self.assertNotEqual(obligation.current_status, "CHECKER_AVAILABLE")
        print("NO_HALLUCINATED_CERTIFICATE_PASS")


if __name__ == "__main__":
    unittest.main()
