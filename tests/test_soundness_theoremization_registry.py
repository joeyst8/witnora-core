import unittest

from witnora_core.theorem_candidates import initial_theorem_candidates


class SoundnessTheoremizationRegistryTest(unittest.TestCase):
    def test_theorem_registry_g9_g13(self):
        candidates = {candidate.id: candidate for candidate in initial_theorem_candidates()}
        for theorem_id in ["TC-057", "TC-058", "TC-059", "TC-060", "TC-061", "TC-062"]:
            self.assertIn(theorem_id, candidates)
            self.assertTrue(candidates[theorem_id].required_proof_obligations)
            self.assertTrue(candidates[theorem_id].forbidden_interpretations)
            self.assertNotIn(candidates[theorem_id].status, {"THEOREM_PROVEN", "COMPLETE", "PNP_PROGRESS", "HARD", "UNKNOWN"})
        self.assertEqual(candidates["TC-057"].status, "FORMAL_PROOF_SKETCH")
        self.assertEqual(candidates["TC-062"].status, "EMPIRICAL_EVIDENCE")
        print("THEOREM_REGISTRY_G9_G13_PASS")


if __name__ == "__main__":
    unittest.main()
