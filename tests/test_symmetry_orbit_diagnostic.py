import unittest

from witnora_core.collapse_theory import build_family_instances, grammar_profiles, run_instance, syntactic_orbit_diagnostic


class SymmetryOrbitDiagnosticTest(unittest.TestCase):
    def test_symmetry_orbit_diagnostic(self):
        instance = build_family_instances(["symmetric-toy"], prefer_official_tseitin=False)[0]
        diagnostic = syntactic_orbit_diagnostic(instance.formula)
        self.assertEqual(diagnostic["diagnostic"], "SYNTACTIC_ORBIT_DIAGNOSTIC")
        self.assertGreaterEqual(diagnostic["largest_orbit_size"], 4)
        self.assertFalse(diagnostic["is_full_automorphism_detection"])
        self.assertFalse(diagnostic["certified_quotient_collapse"])
        print("SYMMETRY_ORBIT_DIAGNOSTIC_PASS")

    def test_pigeonhole_symmetry_signal(self):
        instance = next(item for item in build_family_instances(["pigeonhole"], prefer_official_tseitin=False) if item.instance_id == "php_4_3")
        result = run_instance(instance, grammar_profiles()["G2_SYMMETRY_PROTOTYPE"])
        orbit = result.to_dict()["detected_structures"]["symmetry_orbit"]
        self.assertGreaterEqual(orbit["largest_orbit_size"], 12)
        self.assertEqual(orbit["symmetry_score"], 1.0)
        self.assertFalse(orbit["certified_quotient_collapse"])
        print("PIGEONHOLE_SYMMETRY_SIGNAL_PASS")

    def test_adversarial_near_symmetry_no_false_orbit(self):
        instance = build_family_instances(["adversarial-near-symmetry"], prefer_official_tseitin=False)[0]
        diagnostic = syntactic_orbit_diagnostic(instance.formula)
        merged = [orbit["variables"] for orbit in diagnostic["candidate_orbits"]]
        self.assertIn([1, 2, 3], merged)
        self.assertNotIn([1, 2, 3, 4], merged)
        self.assertLess(diagnostic["symmetry_score"], 1.0)
        self.assertFalse(diagnostic["certified_quotient_collapse"])
        print("ADVERSARIAL_NEAR_SYMMETRY_NO_FALSE_ORBIT_PASS")


if __name__ == "__main__":
    unittest.main()
