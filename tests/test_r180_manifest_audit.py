"""R-179: read-only migration accounting and default-preservation gate."""
import unittest
from scripts.audit_witnora_r180 import audit


class R180ManifestAuditTests(unittest.TestCase):
    def test_manifest_and_proof_defaults(self):
        result=audit()
        self.assertEqual(result["status"],"RESEARCH_AUDIT_PASSED_NOT_RELEASE_APPROVAL")
        self.assertEqual(result["original_python_files_preserved"],560)
        self.assertFalse(result["full_python_to_rust_migration_complete"])
        self.assertGreaterEqual(result["verified_xor_frontier"],180)
        # Historical audit stays valid as the research ledger advances.
        self.assertLessEqual(result["verified_xor_frontier"],500)


if __name__ == "__main__":
    unittest.main()
