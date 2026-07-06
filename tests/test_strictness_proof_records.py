import tempfile
import unittest
from pathlib import Path

from witnora_core.strictness_proof import (
    G1_XOR_UPPER_BOUND_VERIFIED,
    RESTRICTED_STRICTNESS_PROOF_SKETCH,
    run_strictness_proof,
)


class StrictnessProofRecordsTest(unittest.TestCase):
    def test_g1_xor_upper_bound_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_strictness_proof(instances=["tseitin_10"], cap_c=4, out_root=Path(tmp) / "strictness", zip_path="")
        cert = result["xor_upper_bound_certificates"][0]
        self.assertEqual(cert["checker_status"], G1_XOR_UPPER_BOUND_VERIFIED)
        self.assertTrue(cert["extraction_verified"])
        self.assertEqual(cert["sat_or_unsat_result"], "UNSAT")
        print("G1_XOR_UPPER_BOUND_VERIFIED_PASS")

    def test_restricted_strictness_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_strictness_proof(instances=["tseitin_10", "xor_chain_unsat_n5"], cap_c=4, out_root=Path(tmp) / "strictness", zip_path="")
        statuses = {record["strictness_status"] for record in result["strictness_proof_records"]}
        self.assertEqual(statuses, {RESTRICTED_STRICTNESS_PROOF_SKETCH})
        self.assertEqual({record["restricted_prior_grammar"] for record in result["strictness_proof_records"]}, {"G0_WIDTH_C"})
        print("RESTRICTED_STRICTNESS_RECORD_PASS")


if __name__ == "__main__":
    unittest.main()

