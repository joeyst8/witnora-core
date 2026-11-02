"""Offline separator correctness and holdout protection."""
import itertools
import json
import hashlib
import unittest
from pathlib import Path
from time import perf_counter

from scripts.experiment_satlib_syndrome_mitm import (
    benchmark, candidate_natural_separators, exact_separator_counts,
    enumerate_side_syndromes, lift_original_xor_variables, parity_columns,
    source_local_global, split_local_factors, xor_join,
)
from witnora_core.xor import canonical_xor_cnf_clauses


class SyndromeMITMTests(unittest.TestCase):
    def test_separator_removes_all_cross_edges(self):
        variables = tuple(range(1, 7))
        clauses = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6)]
        candidates = candidate_natural_separators(variables, clauses, [], min_side=1)
        cut = next(c for c in candidates if c["cut_after_var"] == 3)
        self.assertEqual(cut["boundary"], (3,))
        self.assertEqual(cut["interior_left_count"], 2)
        self.assertEqual(cut["right_count"], 3)

    def test_holdout_locked(self):
        with self.assertRaises(ValueError):
            benchmark("par32-2-c.cnf.Z")

    def test_separator_join_count_matches_bruteforce(self):
        variables = tuple(range(1, 6))
        clauses = [(1, 2), (-2, 3), (3, -4), (4, 5)]
        local = [((1, 2, 3), 1), ((3, 4, 5), 0)]
        candidates = candidate_natural_separators(variables, clauses, local,
                                                  min_side=1)
        candidate = next(c for c in candidates if c["cut_after_var"] == 3)
        split = split_local_factors(clauses, variables, local, candidate)
        result = exact_separator_counts(split)
        expected = 0
        for bits in itertools.product((0, 1), repeat=5):
            if (all(any(bool(bits[abs(lit) - 1]) == (lit > 0) for lit in clause)
                    for clause in clauses) and
                all(sum(bits[v - 1] for v in row) % 2 == rhs for row, rhs in local)):
                expected += 1
        self.assertEqual(result["local_model_count_from_join"], expected)

    def test_syndrome_join_reconstructs_a_true_local_model(self):
        variables = tuple(range(1, 6))
        clauses = [(1, 2), (-2, 3), (3, -4), (4, 5)]
        local = [((1, 2, 3), 1), ((3, 4, 5), 0)]
        global_rows = [((1, 5), 0), ((2, 4), 1)]
        candidates = candidate_natural_separators(variables, clauses, local,
                                                  min_side=1)
        split = split_local_factors(clauses, variables, local,
                                    next(c for c in candidates if c["cut_after_var"] == 3))
        columns, target = parity_columns(global_rows)
        deadline = perf_counter() + 3
        for b in range(1 << len(split["boundary"])):
            left, _, left_complete, _ = enumerate_side_syndromes(
                split, "left", b, columns, model_limit=100, deadline=deadline)
            right, _, right_complete, _ = enumerate_side_syndromes(
                split, "right", b, columns, model_limit=100, deadline=deadline)
            self.assertTrue(left_complete and right_complete)
            boundary_mask = 0
            boundary_signature = 0
            for j, var in enumerate(split["boundary"]):
                if b & (1 << j):
                    boundary_mask |= 1 << (var - 1)
                    boundary_signature ^= columns.get(var, 0)
            matched = xor_join(left, right, target ^ boundary_signature)
            if matched is not None:
                _, _, _, early = enumerate_side_syndromes(
                    split, "right", b, columns, model_limit=100, deadline=deadline,
                    match_signatures=left,
                    required_syndrome=target ^ boundary_signature)
                self.assertEqual(early, matched)
                bits = [int(bool((matched | boundary_mask) & (1 << v)))
                        for v in range(5)]
                self.assertTrue(all(any(bool(bits[abs(lit) - 1]) == (lit > 0)
                                        for lit in clause) for clause in clauses))
                self.assertTrue(all(sum(bits[v - 1] for v in vars_) % 2 == rhs
                                    for vars_, rhs in local + global_rows))
                break
        else:
            self.fail("small source has a satisfying joined model")

    def test_full_source_auxiliary_lift(self):
        clauses = sorted(canonical_xor_cnf_clauses((1, 2, 3), 1))
        clauses += [(1, 4), (4, -2)]
        lifted = lift_original_xor_variables(
            clauses, 4, {1: True, 2: False, 4: True})
        self.assertFalse(lifted[3])

    def test_reused_source_equations_match_fresh_recovery(self):
        from scripts.experiment_satlib_residual_fourier import source_residual_parity_rows
        clauses = sorted(canonical_xor_cnf_clauses((1, 2, 3), 1))
        clauses += [(1, 4), (4, -2)]
        equations = source_residual_parity_rows(
            clauses, 4, return_source_equations=True)[4]
        given = {1: True, 2: False, 4: True}
        self.assertEqual(lift_original_xor_variables(clauses, 4, given),
                         lift_original_xor_variables(clauses, 4, given,
                                                     source_equations=equations))

    def test_archived_original_witness_digest_and_domain(self):
        path = (Path(__file__).resolve().parent.parent / "research" /
                "PR119_PAR32_1_MITM_VERIFIED_WITNESS.json")
        payload = json.loads(path.read_text(encoding="utf-8"))
        true_vars = payload["positive_original_variable_ids"]
        self.assertEqual(payload["variables"], 1315)
        self.assertEqual(payload["clauses"], 5254)
        self.assertEqual(sorted(set(true_vars)), true_vars)
        self.assertTrue(all(1 <= v <= 1315 for v in true_vars))
        positive = set(true_vars)
        digest = hashlib.sha256(bytes(int(v in positive) for v in range(1, 1316))).hexdigest()
        self.assertEqual(digest, payload["model_boolean_vector_sha256"])


if __name__ == "__main__":
    unittest.main()
