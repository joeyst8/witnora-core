"""R-321–R-340: independent GF2 source provenance and proof fail-closed gates."""

from __future__ import annotations

import copy
import os
import unittest

from scripts.benchmark_xor_syndrome_frontier import (
    evaluate_hypergraph, parity_hypergraph, shortest_inconsistent_subset,
    validate_witness_against_original,
)
from scripts.benchmark_xor_frontier import exhaustive_sat
from witnora_core.cnf import CNFFormula
from witnora_core.drat_check import check_drat_text
from witnora_core.drat_trim import find_drat_trim
from witnora_core.xor import XorEquation, canonical_xor_cnf_clauses
from witnora_core.xor_drat import _row_trace_refutation, _sparse_xor_elimination_schedule


def setup(seed=321):
    formula, equations = parity_hypergraph(seed)
    witness, _ = shortest_inconsistent_subset(equations)
    selected = [equations[index] for index in witness]
    trace = _sparse_xor_elimination_schedule(selected)["row_operation_trace"]
    return formula, equations, witness, selected, trace


def proof_candidate(formula, selected, trace, **overrides):
    return _row_trace_refutation(formula, selected, trace,
        **{**dict(max_proof_clauses=10000, max_proof_bytes=200000,
                 timeout_seconds=None), **overrides})


class XorHypergraphAdversarialTests(unittest.TestCase):
    def test_r321_exact_witness_provenance(self):
        formula, equations, witness, _, _ = setup()
        self.assertTrue(validate_witness_against_original(formula, equations, witness)
                        ["exact_original_source_verified"])

    def test_r322_three_variable_source_encoding(self):
        formula, equations, witness, _, _ = setup(322)
        self.assertTrue(validate_witness_against_original(formula, equations, witness)
                        ["odd_dependency_verified"])

    def test_r323_four_variable_mixed_source_encoding(self):
        rows = [([1,2,3,4],0),([3,4,5],0),([1,2,5],1)]
        equations = [XorEquation(v,r,source_clauses=canonical_xor_cnf_clauses(v,r))
                     for v,r in rows]
        formula = CNFFormula(c for row in equations for c in row.source_clauses)
        self.assertEqual(validate_witness_against_original(formula,equations,(0,1,2))
                         ["witness_rows"],3)

    def test_r324_missing_original_source_clause_rejected(self):
        formula, equations, witness, selected, _ = setup(324)
        support = {tuple(c) for equation in selected for c in equation.source_clauses}
        target = min(support)
        reduced = CNFFormula(c for c in formula.to_clause_lists() if tuple(c) != target)
        with self.assertRaisesRegex(ValueError, "missing from original"):
            validate_witness_against_original(reduced,equations,witness)

    def test_r325_incomplete_source_metadata_rejected(self):
        formula, equations, witness, selected, _ = setup(325)
        index = witness[0]
        old = equations[index]
        equations[index] = XorEquation(old.variables,old.rhs,
            source_clauses=old.source_clauses[1:])
        with self.assertRaisesRegex(ValueError, "incomplete"):
            validate_witness_against_original(formula,equations,witness)

    def test_r326_forged_parity_metadata_rejected(self):
        formula, equations, witness, _, _ = setup(326)
        index = witness[0]
        old = equations[index]
        equations[index] = XorEquation(old.variables,old.rhs ^ 1,
            source_clauses=old.source_clauses)
        with self.assertRaisesRegex(ValueError, "altered"):
            validate_witness_against_original(formula,equations,witness)

    def test_r327_duplicate_row_index_rejected(self):
        formula, equations, witness, _, _ = setup(327)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_witness_against_original(formula,equations,witness + (witness[0],))

    def test_r328_noncanonical_row_index_order_rejected(self):
        formula, equations, witness, _, _ = setup(328)
        with self.assertRaisesRegex(ValueError, "indices"):
            validate_witness_against_original(formula,equations,tuple(reversed(witness)))

    def test_r329_out_of_range_row_rejected(self):
        formula, equations, witness, _, _ = setup(329)
        with self.assertRaisesRegex(ValueError, "outside source"):
            validate_witness_against_original(formula,equations,(len(equations),))

    def test_r330_empty_witness_rejected(self):
        formula, equations, _, _, _ = setup(330)
        with self.assertRaisesRegex(ValueError, "invalid"):
            validate_witness_against_original(formula,equations,())

    def test_r331_consistent_odd_dependency_forgery_rejected(self):
        rows=[XorEquation([1],0,source_clauses=canonical_xor_cnf_clauses([1],0))]
        formula=CNFFormula(c for row in rows for c in row.source_clauses)
        with self.assertRaisesRegex(ValueError, "odd GF2"):
            validate_witness_against_original(formula,rows,(0,))

    def test_r332_exact_dependency_witness_replay(self):
        for seed in range(332000,332032):
            formula, equations, witness, _, _ = setup(seed)
            self.assertTrue(validate_witness_against_original(formula,equations,witness)
                            ["odd_dependency_verified"])

    def test_r333_missing_original_clause_native_candidate_rejects(self):
        formula, _, _, selected, trace = setup(333)
        target = min({tuple(c) for eq in selected for c in eq.source_clauses})
        reduced = CNFFormula(c for c in formula.to_clause_lists() if tuple(c) != target)
        proof, error, _ = proof_candidate(reduced, selected, trace)
        self.assertIsNone(proof)
        self.assertEqual(error,"DETECTED_XOR_SOURCE_CLAUSE_MISSING_FROM_ORIGINAL")

    def test_r334_zero_clause_budget_fails_closed(self):
        formula, _, _, selected, trace = setup(334)
        proof, error, _ = proof_candidate(formula,selected,trace,max_proof_clauses=0)
        self.assertIsNone(proof)
        self.assertEqual(error,"SKIPPED_PROOF_SIZE_CAP")

    def test_r335_zero_byte_budget_fails_closed(self):
        formula, _, _, selected, trace = setup(335)
        proof, error, _ = proof_candidate(formula,selected,trace,max_proof_bytes=0)
        self.assertIsNone(proof)
        self.assertEqual(error,"SKIPPED_PROOF_BYTES_CAP")

    def test_r336_exact_proof_budgets_pass(self):
        formula, _, _, selected, trace = setup(336)
        proof, error, stats = proof_candidate(formula,selected,trace)
        self.assertIsNone(error)
        tight, tight_error, tight_stats = proof_candidate(formula,selected,trace,
            max_proof_clauses=stats["proof_clause_count_actual"],
            max_proof_bytes=stats["proof_file_size_bytes"])
        self.assertEqual((tight,tight_error,tight_stats),(proof,error,stats))

    def test_r337_original_clause_permutation_invariant(self):
        formula, _, _, selected, trace = setup(337)
        shuffled=CNFFormula(reversed(formula.to_clause_lists()))
        self.assertEqual(proof_candidate(formula,selected,trace),
                         proof_candidate(shuffled,selected,trace))

    def test_r338_extra_nonlinear_original_clause_preserves_proof(self):
        formula, _, _, selected, trace = setup(338)
        extended=CNFFormula(list(formula.to_clause_lists())+[[100, -101, 102]])
        proof, error, _ = proof_candidate(extended,selected,trace)
        self.assertIsNone(error)
        self.assertTrue(check_drat_text(extended,proof)["verified"])

    def test_r339_true_sat_control_emits_no_contradictory_witness(self):
        formula, equations = parity_hypergraph(339,contradictory=False)
        self.assertTrue(exhaustive_sat(formula))
        self.assertIsNone(shortest_inconsistent_subset(equations)[0])

    def test_r340_seeded_original_cnf_rup_pass(self):
        for seed in range(340000,340064):
            self.assertGreater(evaluate_hypergraph(seed)["proof_clauses"],0)


@unittest.skipUnless(find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM")),
                     "pinned drat-trim unavailable")
class XorHypergraphExternalTests(unittest.TestCase):
    def test_r321_r340_heldout_external_checker(self):
        checker=find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM"))
        self.assertTrue(all(evaluate_hypergraph(seed,external_checker=checker)
            ["external_drat_verified"] for seed in range(340000,340032)))


class XorHypergraphNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("native Rust extension absent; CI builds it")

    def test_r321_r340_native_hypergraph_differential(self):
        self.assertTrue(all(evaluate_hypergraph(seed,compare_rust=True)
            ["native_differential"] for seed in range(340000,340032)))


if __name__ == "__main__":
    unittest.main()
