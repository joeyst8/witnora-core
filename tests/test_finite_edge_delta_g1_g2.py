import unittest

from witnora_core.finite_edge_certificate import (
    FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED,
    G2_SYMMETRY_CERTIFICATE_VERIFIED,
    LOWER_REPLAY_NO_COLLAPSE,
    NOT_A_DELTA,
    SAT_ASSIGNMENT_VERIFIED,
    candidate_edge_delta_record,
    cycle_coloring_instance,
    replay_lower_g1,
    replay_upper_g2,
)


class FiniteEdgeDeltaG1G2Test(unittest.TestCase):
    def test_lower_replay_no_collapse_not_lower_bound(self):
        instance = cycle_coloring_instance("cycle_4_3color")
        lower = replay_lower_g1(instance)
        self.assertEqual(lower["evidence_type"], LOWER_REPLAY_NO_COLLAPSE)
        self.assertEqual(lower["replay_status"], LOWER_REPLAY_NO_COLLAPSE)
        self.assertIsNone(lower["lower_bound_certificate"])
        self.assertIn("not a lower-bound proof", lower["claim_boundary"])
        print("LOWER_REPLAY_NO_COLLAPSE_PASS")
        print("LOWER_REPLAY_NOT_LOWER_BOUND_PASS")

    def test_upper_g2_symmetry_replay_and_witness(self):
        instance = cycle_coloring_instance("cycle_6_3color")
        upper = replay_upper_g2(instance)
        self.assertEqual(upper["public_category"], SAT_ASSIGNMENT_VERIFIED)
        self.assertEqual(upper["checker_status"], G2_SYMMETRY_CERTIFICATE_VERIFIED)
        self.assertTrue(upper["witness_or_certificate_verified"])
        print("UPPER_G2_SYMMETRY_REPLAY_PASS")
        print("UPPER_G2_WITNESS_VERIFIED_PASS")

    def test_cycle_edge_delta_rows(self):
        markers = {
            "cycle_4_3color": "CYCLE_4_3COLOR_EDGE_DELTA_PASS",
            "cycle_6_3color": "CYCLE_6_3COLOR_EDGE_DELTA_PASS",
            "cycle_8_3color": "CYCLE_8_3COLOR_EDGE_DELTA_PASS",
            "cycle_10_3color": "CYCLE_10_3COLOR_EDGE_DELTA_PASS",
        }
        for instance_id, marker in markers.items():
            record = candidate_edge_delta_record(instance_id)
            self.assertEqual(record.instance_checker_status, FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED)
            self.assertEqual(record.lower_result["evidence_type"], LOWER_REPLAY_NO_COLLAPSE)
            self.assertTrue(record.upper_result["witness_or_certificate_verified"])
            print(marker)

    def test_not_a_delta_if_lower_solves(self):
        record = candidate_edge_delta_record("lower_solves_control")
        self.assertEqual(record.instance_checker_status, NOT_A_DELTA)
        self.assertEqual(record.lower_result["public_category"], SAT_ASSIGNMENT_VERIFIED)
        print("NOT_A_DELTA_IF_LOWER_SOLVES_PASS")


if __name__ == "__main__":
    unittest.main()
