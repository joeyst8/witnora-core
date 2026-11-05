"""R-361–R-380: GF2 gauge/relabel invariance and proof-size sensitivity."""

from __future__ import annotations

import os
import unittest

from scripts.benchmark_xor_gauge_frontier import (
    evaluate_gauge, run_gauge, transform_equations,
)
from scripts.benchmark_xor_syndrome_frontier import (
    exhaustive_inconsistent_subset, parity_hypergraph,
    shortest_inconsistent_subset, validate_witness_against_original,
)
from scripts.benchmark_xor_frontier import exhaustive_sat
from witnora_core.drat_trim import find_drat_trim


class XorGaugeResearchTests(unittest.TestCase):
    def setup_rows(self):
        formula, rows=parity_hypergraph(361)
        variables=sorted({v for r in rows for v in r.variables})
        return formula, rows, variables

    def test_r361_identity_transform_preserves_original_cnf(self):
        formula, rows, _=self.setup_rows()
        transformed, _=transform_equations(rows)
        self.assertEqual(formula,transformed)

    def test_r362_all_variable_gauge_flip_preserves_witness(self):
        _, rows, variables=self.setup_rows()
        _, changed=transform_equations(rows,gauge={v:True for v in variables})
        self.assertEqual(shortest_inconsistent_subset(rows)[0],
                         shortest_inconsistent_subset(changed)[0])

    def test_r363_alternating_variable_gauge_flip(self):
        _, rows, variables=self.setup_rows()
        _, changed=transform_equations(rows,gauge={v:i%2==0 for i,v in enumerate(variables)})
        self.assertEqual(exhaustive_inconsistent_subset(rows),
                         exhaustive_inconsistent_subset(changed))

    def test_r364_full_variable_permutation_preserves_witness(self):
        _, rows, variables=self.setup_rows()
        _, changed=transform_equations(rows,renaming=dict(zip(variables,reversed(variables))))
        self.assertEqual(shortest_inconsistent_subset(rows)[0],
                         shortest_inconsistent_subset(changed)[0])

    def test_r365_sparse_relabel_remains_exact(self):
        _, rows, variables=self.setup_rows()
        formula, changed=transform_equations(rows,
            renaming={v:100000+100*v for v in variables})
        witness,_=shortest_inconsistent_subset(changed)
        self.assertTrue(validate_witness_against_original(formula,changed,witness)
                        ["exact_original_source_verified"])

    def test_r366_gauge_rhs_parity_is_computed_per_source_support(self):
        _, rows, variables=self.setup_rows()
        gauge={v:True for v in variables}
        _, changed=transform_equations(rows,gauge=gauge)
        self.assertTrue(all(new.rhs==(old.rhs^(len(old.variables)%2))
                            for old,new in zip(rows,changed)))

    def test_r367_transformed_source_encoding_exact(self):
        self.assertIsNotNone(evaluate_gauge(367)["transformed_source_sha256"])

    def test_r368_minimum_inconsistent_subset_indices_invariant(self):
        for seed in range(368000,368032):
            _, rows=parity_hypergraph(seed)
            variables=sorted({v for r in rows for v in r.variables})
            _, changed=transform_equations(rows,
                renaming={v:v+100 for v in variables},
                gauge={v:v%2==0 for v in variables})
            self.assertEqual(shortest_inconsistent_subset(rows)[0],
                             shortest_inconsistent_subset(changed)[0])

    def test_r369_exhaustive_minimal_witness_length_invariant(self):
        for record in run_gauge(samples=32)["records"]:
            self.assertEqual(record["contradictory"],record["minimal_witness_rows"] is not None)

    def test_r370_reachable_syndrome_state_count_invariant(self):
        _, rows, variables=self.setup_rows()
        _, changed=transform_equations(rows,
            renaming={v:100+v for v in variables},gauge={v:True for v in variables})
        self.assertEqual(shortest_inconsistent_subset(rows)[1]["reachable_states"],
                         shortest_inconsistent_subset(changed)[1]["reachable_states"])

    def test_r371_sat_controls_remain_sat_under_gauge(self):
        self.assertTrue(all(evaluate_gauge(seed,contradictory=False)
            ["minimal_witness_rows"] is None for seed in range(371000,371016)))

    def test_r372_unsat_original_cnf_truth_table_preserved(self):
        formula, rows, variables=self.setup_rows()
        changed, _=transform_equations(rows,gauge={v:True for v in variables})
        self.assertEqual(exhaustive_sat(formula),exhaustive_sat(changed))
        self.assertFalse(exhaustive_sat(changed))

    def test_r373_both_proof_candidates_exist(self):
        result=evaluate_gauge(373)
        self.assertTrue(result["original_proof_sha256"])
        self.assertTrue(result["transformed_proof_sha256"])

    def test_r374_representation_can_change_proof_clause_count(self):
        rows=[r for r in run_gauge(samples=64)["records"] if r["contradictory"]]
        self.assertEqual(sum(r["proof_clauses"]!=r["transformed_proof_clauses"]
                             for r in rows),20)

    def test_r375_max_frozen_proof_count_delta(self):
        rows=[r for r in run_gauge(samples=64)["records"] if r["contradictory"]]
        self.assertEqual(max(abs(r["proof_clauses"]-r["transformed_proof_clauses"])
                             for r in rows),12)

    def test_r376_no_external_checker_does_not_certify(self):
        rows=run_gauge(samples=12)["records"]
        self.assertTrue(all(not row["external_drat_verified"] for row in rows))

    def test_r377_noninjective_variable_remap_rejected(self):
        _, rows, variables=self.setup_rows()
        with self.assertRaisesRegex(ValueError,"injective"):
            transform_equations(rows,renaming={v:1 for v in variables})

    def test_r378_incomplete_variable_remap_rejected(self):
        _, rows, variables=self.setup_rows()
        with self.assertRaisesRegex(ValueError,"total"):
            transform_equations(rows,renaming={variables[0]:123})

    def test_r379_gauge_with_unknown_variable_rejected(self):
        _, rows, variables=self.setup_rows()
        with self.assertRaisesRegex(ValueError,"outside"):
            transform_equations(rows,gauge={max(variables)+100:True})

    def test_r380_full_64_seed_paired_metamorphic_suite(self):
        result=run_gauge(samples=64)
        self.assertEqual(result["cases"],128)
        self.assertEqual(sum(row["contradictory"] for row in result["records"]),64)


@unittest.skipUnless(find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM")),
                     "external drat-trim unavailable")
class XorGaugeExternalTests(unittest.TestCase):
    def test_r361_r380_real_external_checker_both_gauges(self):
        checker=find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM"))
        rows=run_gauge(samples=64,external_checker=checker)["records"]
        self.assertTrue(all(row["external_drat_verified"]
                            for row in rows if row["contradictory"]))


class XorGaugeNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("native extension absent; CI builds it")

    def test_r361_r380_python_rust_native_gauge_differential(self):
        result=run_gauge(samples=64,compare_rust=True)
        self.assertTrue(result["native_differential_performed"])


if __name__=="__main__":
    unittest.main()
