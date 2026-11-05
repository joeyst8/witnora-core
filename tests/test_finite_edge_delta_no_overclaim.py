import json
import unittest

from witnora_core.finite_edge_certificate import (
    FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED,
    NOT_CLAIMED,
    PROOF_OBLIGATION,
    build_finite_edge_delta_certificate,
)


def _status_values(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_text = str(key)
            if key_text.endswith("status") or key_text in {"status", "checker_status", "evidence_grade"}:
                yield value
            yield from _status_values(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _status_values(item)


class FiniteEdgeDeltaNoOverclaimTest(unittest.TestCase):
    def test_no_strictness_or_family_theorem_claim(self):
        cert = build_finite_edge_delta_certificate(instances=["cycle_4_3color"]).to_dict()
        self.assertEqual(cert["evidence_grade"], FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED)
        self.assertEqual(cert["family_theorem_status"], NOT_CLAIMED)
        self.assertEqual(cert["strictness_theorem_status"], PROOF_OBLIGATION)
        payload = json.dumps(cert, sort_keys=True)
        self.assertNotIn("G1_XOR lower bound proven", payload)
        self.assertNotIn("G1_XOR strictly weaker than G2 as a theorem", payload)
        print("FINITE_EDGE_DELTA_NO_STRICTNESS_THEOREM_CLAIM_PASS")
        print("FINITE_EDGE_DELTA_NO_FAMILY_THEOREM_CLAIM_PASS")

    def test_no_false_lower_bound_or_pnp_or_forbidden_status(self):
        cert = build_finite_edge_delta_certificate(instances=["cycle_4_3color"]).to_dict()
        payload = json.dumps(cert, sort_keys=True)
        self.assertNotIn("lower-bound proof", cert["instances"][0]["lower_result"]["evidence_type"])
        self.assertNotIn("hierarchy completeness is proven", payload)
        self.assertNotIn("proves P vs NP", payload)
        statuses = list(_status_values(cert))
        self.assertNotIn("HARD", statuses)
        self.assertNotIn("UNKNOWN", statuses)
        print("NO_FALSE_LOWER_BOUND_CLAIM_PASS")
        print("NO_HIERARCHY_COMPLETENESS_CLAIM_PASS")
        print("NO_PNP_CLAIM_PASS")
        print("NO_HARD_UNKNOWN_STATUS_PASS")


if __name__ == "__main__":
    unittest.main()
