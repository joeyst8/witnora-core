import unittest

from witnora_core.submit_release_finalize_v226 import (
    citation_coverage_summary,
    final_preprint_text,
    related_work_citation_validation,
)


class CitationCoverageV226Test(unittest.TestCase):
    def test_citation_categories(self):
        summary = citation_coverage_summary()
        self.assertEqual(summary["verification_status"], "PASS")
        self.assertTrue(summary["all_required_categories_covered"])
        markers = {
            "sat_preprocessing": "CITATION_COVERAGE_SAT_PREPROCESSING_PASS",
            "proof_logging": "CITATION_COVERAGE_PROOF_LOGGING_PASS",
            "affine_xor": "CITATION_COVERAGE_AFFINE_XOR_PASS",
            "treewidth_separator": "CITATION_COVERAGE_TREEWIDTH_SEPARATOR_PASS",
            "circuit_cnf": "CITATION_COVERAGE_CIRCUIT_CNF_PASS",
            "sat_portfolio": "CITATION_COVERAGE_SAT_PORTFOLIO_PASS",
            "proof_motif": "CITATION_COVERAGE_PROOF_MOTIF_PASS",
        }
        for category, marker in markers.items():
            self.assertTrue(summary["categories"][category]["covered"])
            print(marker)

    def test_related_work_citation_validation(self):
        validation = related_work_citation_validation(final_preprint_text())
        self.assertEqual(validation["verification_status"], "PASS")
        self.assertEqual(validation["todo_markers"], [])
        self.assertEqual(validation["missing_subsections"], [])
        print("RELATED_WORK_CITATION_VALIDATION_PASS")


if __name__ == "__main__":
    unittest.main()
