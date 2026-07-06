import tempfile
import unittest
from pathlib import Path

from witnora_core.soundness_theoremization import (
    EMPIRICAL_EVIDENCE,
    FORMAL_PROOF_SKETCH,
    PUBLIC_CATEGORY,
    RECORD_TYPE,
    SCOPE,
    THEOREMIZATION_PACKAGE_VERIFIED,
    build_theoremization_record,
    check_soundness_theoremization,
    run_soundness_theoremization,
)


class SoundnessTheoremizationSchemaTest(unittest.TestCase):
    def test_schema_and_scope(self):
        record = build_theoremization_record().to_dict()
        self.assertEqual(record["record_type"], RECORD_TYPE)
        self.assertEqual(record["scope"], SCOPE)
        self.assertEqual(record["status"], THEOREMIZATION_PACKAGE_VERIFIED)
        self.assertEqual(record["public_category"], PUBLIC_CATEGORY)
        self.assertEqual(len(record["theorem_candidates"]), 6)
        self.assertEqual(check_soundness_theoremization(record)["status"], THEOREMIZATION_PACKAGE_VERIFIED)
        print("SOUNDNESS_THEOREMIZATION_SCHEMA_PASS")

    def test_g9_through_g13_candidates_present(self):
        candidates = build_theoremization_record().to_dict()["theorem_candidates"]
        by_scope = {tuple(candidate["grammar_scope"]): candidate for candidate in candidates}
        self.assertIn(("G9_COMPOSED_OPERATOR_ORCHESTRATION_PROTOTYPE",), by_scope)
        self.assertIn(("G10_CIRCUIT_PROJECTION_LIFT_PROTOTYPE",), by_scope)
        self.assertIn(("G11_PROOF_MOTIF_GENERALIZATION_CHECKER_PROTOTYPE",), by_scope)
        self.assertIn(("G12_SELF_EXPANDING_COLLAPSE_PLANNER_PROTOTYPE",), by_scope)
        self.assertIn(("G13_PLANNER_GUIDED_EXECUTION_PROTOTYPE",), by_scope)
        for candidate in candidates[:5]:
            self.assertEqual(candidate["status"], FORMAL_PROOF_SKETCH)
        self.assertEqual(candidates[-1]["status"], EMPIRICAL_EVIDENCE)
        print("SOUNDNESS_THEOREMIZATION_G9_PASS")
        print("SOUNDNESS_THEOREMIZATION_G10_PASS")
        print("SOUNDNESS_THEOREMIZATION_G11_PASS")
        print("SOUNDNESS_THEOREMIZATION_G12_PASS")
        print("SOUNDNESS_THEOREMIZATION_G13_PASS")
        print("CLOSED_LOOP_SOUNDNESS_SKETCH_PASS")

    def test_run_writes_required_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "v221"
            result = run_soundness_theoremization(out_root=out, strict=True, zip_path=None)
            self.assertEqual(result["summary"]["candidate_count"], 6)
            self.assertTrue((out / "soundness_backbone_theoremization.json").exists())
            self.assertTrue((out / "theorem_candidate_summary.json").exists())
            self.assertTrue((out / "evidence_linkage_summary.json").exists())


if __name__ == "__main__":
    unittest.main()
