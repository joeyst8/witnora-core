import unittest

from witnora_core.operator_genesis import (
    GENERATED_CANDIDATE,
    extract_fingerprints,
    generate_operator_candidates,
)


class OperatorCandidateGenerationTest(unittest.TestCase):
    def _candidates(self):
        fingerprints = extract_fingerprints(
            ["pigeonhole", "parity", "graph-coloring", "clique", "subset-sum", "adversarial-mixed", "random-structured"]
        )
        return generate_operator_candidates(fingerprints)

    def test_candidate_generation(self):
        candidates = self._candidates()
        self.assertGreaterEqual(len(candidates), 7)
        names = {candidate.name for candidate in candidates}
        self.assertIn("ORBIT_COUNTING_COLLAPSE", names)
        self.assertIn("CAPACITY_DEFICIT_COLLAPSE", names)
        self.assertIn("MODULAR_RESIDUE_COLLAPSE", names)
        for candidate in candidates:
            self.assertEqual(candidate.status, GENERATED_CANDIDATE)
        print("CANDIDATE_GENERATION_PASS")

    def test_candidate_has_trigger_signature(self):
        for candidate in self._candidates():
            self.assertTrue(candidate.trigger_signature, candidate.name)
        print("CANDIDATE_HAS_TRIGGER_SIGNATURE_PASS")

    def test_candidate_has_certificate_sketch(self):
        for candidate in self._candidates():
            self.assertTrue(candidate.certificate_obligation, candidate.name)
            self.assertIn("Generated candidate is not implemented.", candidate.forbidden_interpretations)
        print("CANDIDATE_HAS_CERTIFICATE_SKETCH_PASS")

    def test_candidate_generation_determinism(self):
        first = [candidate.to_dict() for candidate in self._candidates()]
        second = [candidate.to_dict() for candidate in self._candidates()]
        self.assertEqual(first, second)
        print("CANDIDATE_GENERATION_DETERMINISM_PASS")

    def test_candidate_not_solved(self):
        for candidate in self._candidates():
            text = " ".join(candidate.forbidden_interpretations)
            self.assertIn("has not solved a formula", text)
            self.assertNotEqual(candidate.status, "IMPLEMENTED")
        print("CANDIDATE_NOT_SOLVED_PASS")


if __name__ == "__main__":
    unittest.main()
