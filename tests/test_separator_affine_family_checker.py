import unittest

from witnora_core.separator_affine_family_theorem import (
    SAT_CERTIFIED,
    UNSAT_CERTIFIED,
    SEPARATOR_AFFINE_CERTIFICATE_VERIFIED,
    build_separator_affine_certificate,
    check_separator_affine_certificate,
    make_separator_affine_instance,
)


class SeparatorAffineFamilyCheckerTest(unittest.TestCase):
    def _checked(self, instance_id):
        instance = make_separator_affine_instance(instance_id)
        cert = build_separator_affine_certificate(instance)
        check = check_separator_affine_certificate(instance.formula, cert)
        self.assertEqual(check["checker_status"], SEPARATOR_AFFINE_CERTIFICATE_VERIFIED)
        return instance, cert.to_dict(), check

    def test_sat_witness_lift(self):
        instance, data, check = self._checked("saf_sat_chain_8")
        self.assertEqual(check["final_result"], SAT_CERTIFIED)
        self.assertTrue(data["sat_witness"]["verified_against_original_cnf"])
        self.assertIsNotNone(data["sat_witness"]["chosen_separator_assignment"])
        print("SEPARATOR_AFFINE_SAT_WITNESS_PASS")

    def test_unsat_cover(self):
        instance, data, check = self._checked("saf_unsat_cover_8")
        self.assertEqual(check["final_result"], UNSAT_CERTIFIED)
        self.assertTrue(data["unsat_cover"]["every_separator_assignment_covered"])
        self.assertEqual(
            len(data["unsat_cover"]["covering_unsat_component_per_assignment"]),
            len(data["separator_assignments"]),
        )
        print("SEPARATOR_AFFINE_UNSAT_COVER_PASS")

    def test_mixed_family_sat_rule_uses_one_all_sat_assignment(self):
        _instance, data, check = self._checked("saf_mixed_components_6")
        self.assertEqual(check["final_result"], SAT_CERTIFIED)
        all_sat_rows = [
            row
            for row in data["separator_assignments"]
            if row["assignment_result"] == "ALL_COMPONENTS_SAT"
        ]
        self.assertGreaterEqual(len(all_sat_rows), 1)
        self.assertTrue(data["sat_witness"]["verified_against_original_cnf"])


if __name__ == "__main__":
    unittest.main()
