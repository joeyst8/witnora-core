import unittest

from witnora_core.finite_edge_certificate import FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED
from witnora_core.finite_strictness_certificate import FINITE_STRICTNESS_CERTIFIED
from witnora_core.paper_hardening import reviewer_objection_table_text
from witnora_core.reproducibility_package import evidence_summary_records


class V213ReviewerObjectionTableTest(unittest.TestCase):
    def test_evidence_grades_preserved(self):
        grades = {record.hierarchy_edge: record.evidence_type for record in evidence_summary_records()}
        self.assertEqual(grades["G0_WIDTH_C -> G1_XOR_FOR_STRICTNESS"], FINITE_STRICTNESS_CERTIFIED)
        self.assertEqual(grades["G1_XOR -> G2_SYMMETRY_CERTIFIED"], FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED)
        print("EVIDENCE_GRADES_PRESERVED_PASS")

    def test_finite_edge_delta_not_strictness(self):
        table = reviewer_objection_table_text()
        self.assertIn("Empirical edge deltas are not lower bounds.", table)
        self.assertIn("FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED", table)
        self.assertNotIn("G1_XOR is strictly weaker than G2_SYMMETRY_CERTIFIED", table)
        print("FINITE_EDGE_DELTA_NOT_STRICTNESS_PASS")

    def test_native_cert_not_drat(self):
        table = reviewer_objection_table_text()
        self.assertIn("Native certificates are not DRAT.", table)
        self.assertIn("DRAT is only claimed when exported and externally checked", table)
        print("NATIVE_CERT_NOT_DRAT_PASS")


if __name__ == "__main__":
    unittest.main()
