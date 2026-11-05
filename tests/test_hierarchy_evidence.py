import tempfile
import unittest
from pathlib import Path

from witnora_core.hierarchy_formalization import (
    NOT_RECORDED,
    build_hierarchy_theoremization,
    hierarchy_evidence_bundle,
    theorem_candidates_v28,
)


class HierarchyEvidenceTest(unittest.TestCase):
    def test_theorem_candidate_formulation(self):
        candidates = theorem_candidates_v28()
        self.assertGreaterEqual(len(candidates), 10)
        self.assertTrue(any(item.name == "Collapse Hierarchy Strictness Program" for item in candidates))
        self.assertFalse(any(item.current_status == "PROVEN" for item in candidates))
        print("THEOREM_CANDIDATE_FORMULATION_PASS")
        print("PROVEN_REQUIRES_PROOF_FILE_PASS")

    def test_evidence_bundle(self):
        bundle = hierarchy_evidence_bundle().to_dict()
        self.assertIn("v2.7-proof-motif-compression", bundle["release_tags"])
        self.assertEqual(bundle["source_archive_sha256"]["v2.0-collapse-theory-lab"], NOT_RECORDED)
        self.assertIn("no P vs NP progress claim", bundle["claim_boundaries"]["p_vs_np"])
        print("EVIDENCE_BUNDLE_PASS")

    def test_reports_nonclaims(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "theoremization"
            build_hierarchy_theoremization(out_root=root, zip_path="")
            report = (root / "COLLAPSE_HIERARCHY_THEOREMIZATION_REPORT.md").read_text(encoding="utf-8")
        self.assertIn("This work does not prove P vs NP.", report)
        self.assertIn("Strictness results are empirical unless marked with a formal proof.", report)
        self.assertIn("Native certificates are not DRAT unless explicitly exported and checked.", report)
        self.assertIn("The hierarchy is a research program, not a complete SAT algorithm.", report)
        print("NATIVE_CERT_NOT_DRAT_PASS")
        print("NO_FALSE_HIERARCHY_COMPLETENESS_CLAIM_PASS")
        print("NO_PNP_CLAIM_PASS")


if __name__ == "__main__":
    unittest.main()

