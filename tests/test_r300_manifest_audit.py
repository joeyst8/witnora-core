"""R-300 signed research frontier accounting and fail-closed trust gates."""

import unittest

from scripts.audit_witnora_r300 import audit


class R300ManifestAuditTests(unittest.TestCase):
    def test_r300_gap_free_accounting_and_preserved_proof_boundaries(self):
        result = audit()
        self.assertEqual(result["status"], "R300_RESEARCH_AUDIT_PASSED_NOT_RELEASE_APPROVAL")
        self.assertEqual(result["verified_xor_frontier"], 300)
        self.assertEqual(result["named_post_r180_gate_count"], 119)
        self.assertEqual(result["original_python_files_preserved"], 560)
        self.assertFalse(result["full_python_to_rust_migration_complete"])
        self.assertFalse(result["external_checker_ci_run_verified_by_this_read_only_audit"])
        self.assertTrue(result["lean_kernel_unmodified_by_audit"])


if __name__ == "__main__":
    unittest.main()
