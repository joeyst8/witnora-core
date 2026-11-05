"""R-481–R-500: read-only reproducibility and research-scope sign-off."""

from __future__ import annotations

import inspect
import json
import unittest

from scripts.audit_witnora_r180 import ROOT, audit as old_audit
from scripts.audit_witnora_r300 import audit as prior_audit
from scripts.audit_witnora_r500 import (
    BENCHMARK_SCRIPTS, DOCUMENTS, EXTERNAL_VERIFIER_REVISION,
    TEST_SUITES, audit, named_gates,
)
from witnora_core.xor_drat import export_xor_drat_for_path


class R500ResearchAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = old_audit()
        cls.manifest = json.loads((ROOT / "research/python_to_rust_manifest.json").read_text())

    def test_r481_original_python_source_count(self):
        self.assertEqual(self.baseline["original_python_files_preserved"], 560)

    def test_r482_non_migrated_count(self):
        # R-500's baseline was 470; later verified migration waves lower it.
        self.assertLessEqual(self.baseline["status_counts"]["not_migrated"], 470)

    def test_r483_parallel_reference_count(self):
        self.assertGreaterEqual(self.baseline["status_counts"]["parallel_reference"], 76)

    def test_r484_partially_native_verified_count(self):
        self.assertGreaterEqual(self.baseline["status_counts"]["partial_native_verified"], 14)

    def test_r485_python_still_default(self):
        self.assertEqual(inspect.signature(export_xor_drat_for_path)
                         .parameters["proof_backend"].default, "python")

    def test_r486_native_export_opt_in(self):
        self.assertFalse(inspect.signature(export_xor_drat_for_path)
                         .parameters["require_native_proof_audit"].default)

    def test_r487_dual_source_parser_opt_in(self):
        self.assertFalse(inspect.signature(export_xor_drat_for_path)
                         .parameters["require_dual_source_parser"].default)

    def test_r488_source_identity_opt_in(self):
        self.assertFalse(inspect.signature(export_xor_drat_for_path)
                         .parameters["require_source_identity"].default)

    def test_r489_milestone_frontier_500_gap_free(self):
        self.assertEqual(self.baseline["verified_xor_frontier"], 500)

    def test_r490_historical_r300_audit_preserved(self):
        self.assertEqual(prior_audit()["named_post_r180_gate_count"], 119)

    def test_r491_post_r300_named_gate_count(self):
        self.assertEqual(len(named_gates()), 199)

    def test_r492_post_r300_named_contiguous(self):
        self.assertEqual(set(named_gates()), set(range(301, 500)))

    def test_r493_focused_native_suites_wired(self):
        workflow = (ROOT / ".github/workflows/rust-migration-fast.yml").read_text()
        self.assertTrue(all(suite in workflow for suite in TEST_SUITES))

    def test_r494_pinned_independent_drat_trim_wired(self):
        workflow = (ROOT / ".github/workflows/rust-migration-fast.yml").read_text()
        self.assertIn(EXTERNAL_VERIFIER_REVISION, workflow)

    def test_r495_all_benchmarks_wired(self):
        workflow = (ROOT / ".github/workflows/rust-migration-fast.yml").read_text()
        for path in BENCHMARK_SCRIPTS:
            self.assertIn(path.replace("/", ".").removesuffix(".py"), workflow)

    def test_r496_research_docs_preserved(self):
        self.assertTrue(all((ROOT / path).is_file() for path in DOCUMENTS))

    def test_r497_manifest_xor_remains_partial(self):
        xor = next(e for e in self.manifest["entries"]
                   if e["path"] == "witnora_core/xor_drat.py")
        self.assertEqual(xor["status"], "partial_native_verified")

    def test_r498_research_branch_not_main(self):
        self.assertEqual(self.manifest["branch"], "research/w-crc-001-asymmetric-v1")

    def test_r499_static_ci_claim_not_fabricated(self):
        report = audit()
        self.assertFalse(report["ci_run_verified_by_this_read_only_audit"])

    def test_r500_read_only_research_signoff(self):
        report = audit()
        self.assertEqual(report["status"], "R500_RESEARCH_AUDIT_PASSED_NOT_RELEASE_APPROVAL")
        self.assertEqual(report["named_post_r300_gates"], 199)
        self.assertFalse(report["full_python_to_rust_migration_complete"])
        self.assertFalse(report["p_vs_np_or_general_sat_claim"])


if __name__ == "__main__":
    unittest.main()
