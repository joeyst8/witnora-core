import unittest

from witnora_core.reproducibility_package import (
    evidence_summary_markdown,
    evidence_summary_records,
)


class EvidenceSummaryTest(unittest.TestCase):
    def test_evidence_summary_grades(self):
        records = evidence_summary_records()
        grades = {record.hierarchy_edge: record.evidence_type for record in records}
        self.assertEqual(grades["G0_WIDTH_C -> G1_XOR_FOR_STRICTNESS"], "FINITE_STRICTNESS_CERTIFIED")
        self.assertEqual(grades["G1_XOR -> G2_SYMMETRY_CERTIFIED"], "FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED")
        for edge in [
            "G2_SYMMETRY_CERTIFIED -> G3_SYMMETRY_CARDINALITY_CERTIFIED",
            "G3_SYMMETRY_CARDINALITY_CERTIFIED -> G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE",
            "G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE -> G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE",
            "G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE -> G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE",
        ]:
            self.assertEqual(grades[edge], "EMPIRICAL_EVIDENCE_NOT_THEOREM")
        print("EVIDENCE_SUMMARY_GRADES_PASS")

    def test_finite_summaries(self):
        markdown = evidence_summary_markdown(evidence_summary_records())
        self.assertIn("certified width obstruction", markdown)
        self.assertIn("bounded replay no-collapse", markdown)
        self.assertIn("finite empirical edge delta only", markdown)
        print("FINITE_STRICTNESS_G0_G1_SUMMARY_PASS")
        print("FINITE_EDGE_DELTA_G1_G2_SUMMARY_PASS")


if __name__ == "__main__":
    unittest.main()
