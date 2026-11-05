"""R-381–R-400: exact GF2 syndrome and original-CNF proof budget gates."""

from __future__ import annotations

import os
import unittest

from scripts.benchmark_xor_constraint_geometry import geometry
from scripts.benchmark_xor_frontier import _external_check,exhaustive_sat
from scripts.benchmark_xor_resource_frontier import measure_cap,run_resource
from scripts.benchmark_xor_syndrome_frontier import shortest_inconsistent_subset
from witnora_core.drat_trim import find_drat_trim
from witnora_core.xor_drat import _row_trace_refutation,_sparse_xor_elimination_schedule


class XorResourceResearchTests(unittest.TestCase):
    def assert_size(self,n):
        result=measure_cap(n)
        self.assertEqual(result["gf2_states"],2**n)
        self.assertEqual(result["proof_clauses"],2*n-1)
        self.assertTrue(result["state_under_cap_rejected"])
        self.assertTrue(result["proof_under_caps_rejected"])

    def test_r381_cycle_n4_caps(self): self.assert_size(4)
    def test_r382_cycle_n6_caps(self): self.assert_size(6)
    def test_r383_cycle_n8_caps(self): self.assert_size(8)
    def test_r384_cycle_n10_caps(self): self.assert_size(10)
    def test_r385_cycle_n12_caps(self): self.assert_size(12)
    def test_r386_cycle_n14_caps(self): self.assert_size(14)
    def test_r387_cycle_n16_caps(self): self.assert_size(16)

    def test_r388_one_under_syndrome_state_cap_rejects(self):
        _, rows=geometry(16,"cycle")
        with self.assertRaisesRegex(ValueError,"state cap"):
            shortest_inconsistent_subset(rows,max_states=65535)

    def test_r389_exact_syndrome_state_cap_succeeds(self):
        _, rows=geometry(16,"cycle")
        witness,stats=shortest_inconsistent_subset(rows,max_states=65536)
        self.assertEqual(len(witness),16)
        self.assertEqual(stats["peak_states"],65536)

    def test_r390_one_under_row_count_cap_rejects(self):
        _, rows=geometry(10,"cycle")
        with self.assertRaisesRegex(ValueError,"row cap"):
            shortest_inconsistent_subset(rows,max_rows=9)

    def test_r391_exact_row_count_cap_succeeds(self):
        _, rows=geometry(10,"cycle")
        self.assertEqual(len(shortest_inconsistent_subset(rows,max_rows=10)[0]),10)

    def test_r392_one_under_variable_count_cap_rejects(self):
        _, rows=geometry(10,"cycle")
        with self.assertRaisesRegex(ValueError,"variable cap"):
            shortest_inconsistent_subset(rows,max_variables=9)

    def test_r393_exact_variable_count_cap_succeeds(self):
        _, rows=geometry(10,"cycle")
        self.assertEqual(len(shortest_inconsistent_subset(rows,max_variables=10)[0]),10)

    def test_r394_nonpositive_state_cap_rejects(self):
        _, rows=geometry(8,"cycle")
        for cap in (-1,0):
            with self.assertRaisesRegex(ValueError,"positive"):
                shortest_inconsistent_subset(rows,max_states=cap)

    def test_r395_consistent_cycle_has_no_contradiction(self):
        formula,rows=geometry(8,"cycle",contradictory=False)
        self.assertTrue(exhaustive_sat(formula))
        self.assertIsNone(shortest_inconsistent_subset(rows)[0])

    def test_r396_invalid_explicit_external_path_rejects(self):
        with self.assertRaisesRegex(ValueError,"unavailable"):
            run_resource(maximum_n=4,external_checker="/missing/drat-trim")

    def test_r397_absent_external_checker_is_not_certification(self):
        result=run_resource(maximum_n=10)
        self.assertFalse(result["external_drat_verification_performed"])
        self.assertTrue(all(not row["external_drat_verified"] for row in result["rows"]))

    def test_r398_mismatched_original_cnf_has_sat_control(self):
        original,_=geometry(4,"cycle",contradictory=True)
        satisfiable,_=geometry(4,"cycle",contradictory=False)
        self.assertFalse(exhaustive_sat(original))
        self.assertTrue(exhaustive_sat(satisfiable))

    def test_r399_exact_proof_cap_succeeds_without_external(self):
        row=measure_cap(16)
        self.assertEqual((row["proof_clauses"],row["proof_bytes"]),(31,249))

    def test_r400_all_seven_bounded_resource_levels(self):
        result=run_resource(maximum_n=16)
        self.assertEqual(len(result["rows"]),7)
        self.assertEqual(result["rows"][-1]["gf2_states"],65536)


@unittest.skipUnless(find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM")),
                     "external drat-trim unavailable")
class XorResourceExternalTests(unittest.TestCase):
    def test_r381_r400_real_drat_trim_accepts_each_level(self):
        checker=find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM"))
        result=run_resource(external_checker=checker)
        self.assertTrue(all(row["external_drat_verified"] for row in result["rows"]))

    def test_group_r398_real_drat_trim_rejects_same_proof_on_sat_cnf(self):
        checker=find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM"))
        original,rows=geometry(4,"cycle",contradictory=True)
        sat,_=geometry(4,"cycle",contradictory=False)
        witness,_=shortest_inconsistent_subset(rows)
        selected=[rows[i] for i in witness]
        trace=_sparse_xor_elimination_schedule(selected)["row_operation_trace"]
        proof,error,_=_row_trace_refutation(original,selected,trace,
            max_proof_clauses=2000,max_proof_bytes=40000,timeout_seconds=None)
        self.assertIsNone(error)
        self.assertTrue(_external_check(original,proof,checker))
        self.assertFalse(_external_check(sat,proof,checker))


class XorResourceNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("native Rust extension absent; CI builds it")

    def test_r381_r400_exact_native_python_proof(self):
        result=run_resource(compare_rust=True)
        self.assertTrue(all(row["native_differential"] for row in result["rows"]))


if __name__=="__main__":
    unittest.main()
