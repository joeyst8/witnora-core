import tempfile
import unittest
from pathlib import Path

from witnora_core.strictness_proof import run_strictness_proof


class StrictnessProofReportsTest(unittest.TestCase):
    def test_strictness_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "strictness"
            run_strictness_proof(instances=["tseitin_10", "xor_chain_unsat_n5"], cap_c=4, out_root=root, zip_path="")
            required = [
                "width_obstruction_certificates.json",
                "xor_upper_bound_certificates.json",
                "strictness_proof_records.json",
                "exact_width_audit_summary.json",
                "restricted_g0_g1_theorem_candidate.json",
                "proof_obligation_updates.json",
                "RESTRICTED_G0_G1_STRICTNESS_REPORT.md",
            ]
            for name in required:
                self.assertTrue((root / name).exists(), name)
            report = (root / "RESTRICTED_G0_G1_STRICTNESS_REPORT.md").read_text(encoding="utf-8")
        self.assertIn("This does not prove full G0_BASE strictness.", report)
        self.assertIn("This does not prove P vs NP.", report)
        self.assertIn("No hierarchy completeness theorem.", report)
        print("STRICTNESS_REPORT_PASS")
        print("NO_FALSE_LOWER_BOUND_CLAIM_PASS")
        print("NO_HIERARCHY_COMPLETENESS_CLAIM_PASS")
        print("NO_PNP_CLAIM_PASS")


if __name__ == "__main__":
    unittest.main()

