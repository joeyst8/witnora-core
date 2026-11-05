import tempfile
import unittest
from pathlib import Path

from witnora_core.tc063_theorem_hardening import (
    HARDENED_STATUS,
    TC063_THEOREM_HARDENING_VERIFIED,
    build_hardening_record,
    check_tc063_hardening,
    run_tc063_theorem_hardening,
)
from witnora_core.theorem_candidates import initial_theorem_candidates


class TC063TheoremHardeningSchemaTest(unittest.TestCase):
    def test_hardening_schema(self):
        record = build_hardening_record().to_dict()
        self.assertEqual(record["type"], "TC063_THEOREM_HARDENING_RECORD")
        self.assertEqual(record["theorem_id"], "TC-063")
        self.assertEqual(record["hardened_status"], HARDENED_STATUS)
        self.assertEqual(len(record["lemmas"]), 8)
        check = check_tc063_hardening(record)
        self.assertEqual(check["checker_status"], TC063_THEOREM_HARDENING_VERIFIED)
        print("TC063_HARDENING_SCHEMA_PASS")

    def test_status_update(self):
        candidates = {candidate.id: candidate for candidate in initial_theorem_candidates()}
        tc063 = candidates["TC-063"]
        self.assertEqual(tc063.status, HARDENED_STATUS)
        self.assertEqual(tc063.lemma_count, 8)
        self.assertEqual(tc063.proof_obligation_count, 32)
        self.assertTrue(tc063.dependency_on_g5_affine_soundness)
        self.assertTrue(tc063.fixed_c_polynomiality)
        self.assertTrue(tc063.native_certificate_only)
        self.assertTrue(tc063.external_proof_bridge_absent)
        self.assertTrue(tc063.finite_tests_are_support_only)
        print("TC063_STATUS_UPDATE_PASS")

    def test_run_writes_required_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "v223"
            result = run_tc063_theorem_hardening(out, strict=True, zip_path=None)
            self.assertEqual(result["check"]["checker_status"], TC063_THEOREM_HARDENING_VERIFIED)
            self.assertTrue((out / "tc063_theorem_hardening.json").exists())
            self.assertTrue((out / "tc063_proof_obligation_matrix.json").exists())
            self.assertTrue((out / "TC063_THEOREM_HARDENING_REPORT.md").exists())


if __name__ == "__main__":
    unittest.main()
