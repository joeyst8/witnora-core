import unittest
from dataclasses import replace

from witnora_core.operator_genesis import (
    GENERATED_CANDIDATE,
    PROMOTION_ELIGIBLE,
    REJECTED_NO_CERTIFICATE_SKETCH,
    REJECTED_UNSAFE,
    build_promotion_queue,
    evaluate_promotion,
    extract_fingerprints,
    generate_operator_candidates,
)


class OperatorPromotionPipelineTest(unittest.TestCase):
    def _base_candidate(self):
        fingerprints = extract_fingerprints(["pigeonhole", "parity", "graph-coloring"])
        return generate_operator_candidates(fingerprints)[0]

    def test_promotion_requires_certificate_sketch(self):
        candidate = replace(self._base_candidate(), certificate_obligation=[])
        record = evaluate_promotion(candidate, "test-run")
        self.assertFalse(record.promotion_allowed)
        self.assertEqual(record.to_status, REJECTED_NO_CERTIFICATE_SKETCH)
        self.assertIn("certificate_obligation", record.missing_requirements)
        print("PROMOTION_REQUIRES_CERTIFICATE_SKETCH_PASS")

    def test_promotion_rejects_unsafe(self):
        candidate = replace(self._base_candidate(), safety_risks=["UNSAFE: no preservation argument"])
        record = evaluate_promotion(candidate, "test-run")
        self.assertFalse(record.promotion_allowed)
        self.assertEqual(record.to_status, REJECTED_UNSAFE)
        print("PROMOTION_REJECTS_UNSAFE_PASS")

    def test_promotion_clearly_labeled(self):
        candidate = self._base_candidate()
        self.assertEqual(candidate.status, GENERATED_CANDIDATE)
        record = build_promotion_queue([candidate], "test-run")[0]
        self.assertEqual(record.to_status, PROMOTION_ELIGIBLE)
        self.assertIn("not implemented operators", record.claim_boundary)
        self.assertIn("no implemented or certified claim", " ".join(record.reasons))
        print("PROMOTION_CLEARLY_LABELED_PASS")


if __name__ == "__main__":
    unittest.main()
