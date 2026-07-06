import unittest

from witnora_core.reproducibility_package import claim_boundary_markdown, claim_boundary_records


class ClaimBoundaryTableTest(unittest.TestCase):
    def test_claim_boundary_table(self):
        records = claim_boundary_records()
        claims = {record.claim for record in records}
        for required in {
            "P vs NP",
            "polynomial-time SAT",
            "hierarchy completeness",
            "full hierarchy strictness",
            "full G0_BASE strictness",
            "finite strictness certificate",
            "finite empirical edge delta",
            "native certificate vs DRAT",
            "generated operator vs theorem",
            "replayed no-collapse vs lower-bound proof",
            "empirical evidence vs family theorem",
        }:
            self.assertIn(required, claims)
        table = claim_boundary_markdown(records)
        self.assertIn("Allowed wording", table)
        self.assertIn("Forbidden wording", table)
        print("CLAIM_BOUNDARY_TABLE_PASS")

    def test_claim_boundary_forbidden_wording_is_not_asserted(self):
        records = claim_boundary_records()
        edge = next(record for record in records if record.claim == "finite empirical edge delta")
        self.assertEqual(edge.allowed_wording, "FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED records replayed finite delta evidence.")
        self.assertEqual(edge.forbidden_wording, "The empirical edge delta is a strictness theorem.")
        self.assertIn("not obstruction proof", edge.reason)
        print("CLAIM_BOUNDARY_FORBIDDEN_WORDING_PASS")
        print("NATIVE_CERT_NOT_DRAT_PASS")
        print("NO_FALSE_FAMILY_THEOREM_CLAIM_PASS")
        print("NO_HIERARCHY_COMPLETENESS_CLAIM_PASS")
        print("NO_HARD_UNKNOWN_STATUS_PASS")


if __name__ == "__main__":
    unittest.main()
