import tempfile
import unittest
from pathlib import Path

from witnora_core.finite_strictness_certificate import (
    FINITE_STRICTNESS_CERTIFICATE_VERIFIED,
    FINITE_STRICTNESS_CERTIFIED,
    build_outputs,
)
from witnora_core.strictness_proof import (
    G1_XOR_UPPER_BOUND_VERIFIED,
    RESTRICTED_G0_WIDTH_ROUTE_REJECTED,
    WIDTH_OBSTRUCTION_VERIFIED,
)


class FiniteStrictnessInstancesTest(unittest.TestCase):
    def test_finite_strictness_width_and_xor_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = build_outputs(
                instances=["tseitin_10", "xor_chain_unsat_n5", "tseitin_12", "xor_chain_unsat_n7"],
                cap_c=4,
                out_root=Path(tmp) / "finite",
                zip_path="",
            )
        self.assertEqual(result["finite_strictness_checker_result"]["checker_status"], FINITE_STRICTNESS_CERTIFICATE_VERIFIED)
        self.assertEqual(result["finite_strictness_certificate"]["strictness_status"], FINITE_STRICTNESS_CERTIFIED)
        for record in result["instance_strictness_records"]:
            self.assertEqual(record["lower_result"]["width_obstruction_certificate"]["checker_status"], WIDTH_OBSTRUCTION_VERIFIED)
            self.assertEqual(record["lower_result"]["restricted_route_result"], RESTRICTED_G0_WIDTH_ROUTE_REJECTED)
            self.assertGreater(record["lower_result"]["certified_lower_bound"], 4)
            self.assertEqual(record["upper_result"]["xor_upper_bound_certificate"]["checker_status"], G1_XOR_UPPER_BOUND_VERIFIED)
            self.assertTrue(record["upper_result"]["extraction_verified"])
        print("FINITE_STRICTNESS_WIDTH_REPLAY_PASS")
        print("FINITE_STRICTNESS_XOR_REPLAY_PASS")

    def test_default_finite_instances_include_additions(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = build_outputs(out_root=Path(tmp) / "finite", zip_path="")
        certified = [record["instance_id"] for record in result["instance_strictness_records"]]
        self.assertGreaterEqual(len(certified), 5)
        self.assertIn("tseitin_12", certified)
        self.assertIn("tseitin_14", certified)
        self.assertIn("xor_chain_unsat_n7", certified)


if __name__ == "__main__":
    unittest.main()
