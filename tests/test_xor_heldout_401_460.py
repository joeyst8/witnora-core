"""R-401–R-460: heldout original-CNF and independent rank audits.

These are finite research checks, not general SAT complexity claims.
"""

from __future__ import annotations

import os
import random
import unittest

from scripts.benchmark_xor_frontier import _external_check, exhaustive_sat
from scripts.benchmark_xor_heldout_401_460 import (
    background_instance, disconnected_instance, evaluate_heldout,
    gaussian_dependency_baseline,
)
from scripts.benchmark_xor_syndrome_frontier import (
    shortest_inconsistent_subset, validate_witness_against_original,
)
from witnora_core.cnf import CNFFormula
from witnora_core.drat_trim import find_drat_trim
from witnora_core.xor import XorEquation, canonical_xor_cnf_clauses


def _case(seed=401, *, bad=True):
    return background_instance(seed, contradictory=bad)


class BackgroundCnfTests(unittest.TestCase):
    def test_r401_sat_planted_original_formula(self):
        f, _, _ = _case(bad=False)
        self.assertTrue(exhaustive_sat(f))

    def test_r402_unsat_original_formula(self):
        f, _, _ = _case()
        self.assertFalse(exhaustive_sat(f))

    def test_r403_background_produces_new_clauses(self):
        _, _, info = _case()
        self.assertEqual(info["background_clauses"], 13)

    def test_r404_overlapping_background_variables(self):
        f, rows, _ = _case()
        source = {tuple(c) for row in rows for c in row.source_clauses}
        extras = [c for c in f.to_clause_lists() if tuple(c) not in source]
        self.assertTrue(any(any(abs(x) <= 6 for x in c) for c in extras))

    def test_r405_fresh_variable_background(self):
        f, _, _ = _case()
        self.assertIn(10, f.variables)

    def test_r406_witness_survives_unrelated_cnf(self):
        f, rows, _ = _case()
        witness, _ = shortest_inconsistent_subset(rows)
        self.assertTrue(validate_witness_against_original(f, rows, witness)["odd_dependency_verified"])

    def test_r407_missing_source_clause_detected(self):
        f, rows, _ = _case()
        witness, _ = shortest_inconsistent_subset(rows)
        target = rows[witness[0]].source_clauses[0]
        altered = CNFFormula(c for c in f.to_clause_lists() if tuple(c) != tuple(target))
        with self.assertRaisesRegex(ValueError, "missing from original"):
            validate_witness_against_original(altered, rows, witness)

    def test_r408_mutated_source_rhs_rejected(self):
        f, rows, _ = _case()
        witness, _ = shortest_inconsistent_subset(rows)
        i = witness[0]
        previous = rows[i]
        rows[i] = XorEquation(previous.variables, previous.rhs ^ 1,
                              source_clauses=previous.source_clauses)
        with self.assertRaisesRegex(ValueError, "altered"):
            validate_witness_against_original(f, rows, witness)

    def test_r409_sat_has_no_contradictory_witness(self):
        _, rows, _ = _case(bad=False)
        self.assertIsNone(shortest_inconsistent_subset(rows)[0])

    def test_r410_unsat_original_cnf_internal_rup(self):
        self.assertGreater(evaluate_heldout(410, family="background")["proof_clauses"], 0)

    def test_r411_original_clause_permutation(self):
        f, rows, _ = _case()
        shuffled = CNFFormula(reversed(f.to_clause_lists()))
        witness, _ = shortest_inconsistent_subset(rows)
        self.assertTrue(validate_witness_against_original(shuffled, rows, witness)["exact_original_source_verified"])

    def test_r412_seeded_background_sat_controls(self):
        for seed in range(41200, 41208):
            self.assertFalse(evaluate_heldout(seed, family="background", contradictory=False)["unsatisfiable"])

    def test_r413_seeded_background_unsat_controls(self):
        for seed in range(41300, 41308):
            self.assertGreater(evaluate_heldout(seed, family="background")["proof_clauses"], 0)

    def test_r414_gaussian_agrees_with_background_sat(self):
        _, rows, _ = _case(bad=False)
        self.assertFalse(gaussian_dependency_baseline(rows)["unsatisfiable"])

    def test_r415_gaussian_agrees_with_background_unsat(self):
        _, rows, _ = _case()
        self.assertTrue(gaussian_dependency_baseline(rows)["unsatisfiable"])

    def test_r416_syndrome_count_matches_background_rank(self):
        _, rows, _ = _case()
        self.assertEqual(shortest_inconsistent_subset(rows)[1]["reachable_states"],
                         gaussian_dependency_baseline(rows)["theoretical_states"])

    def test_r417_repeated_seed_is_deterministic(self):
        self.assertEqual(_case(417), _case(417))

    def test_r418_sparse_original_overlap_controls(self):
        for seed in range(41800, 41808):
            f, rows, _ = _case(seed)
            witness, _ = shortest_inconsistent_subset(rows)
            self.assertTrue(validate_witness_against_original(f, rows, witness)["odd_dependency_verified"])

    def test_r419_unknown_family_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown heldout"):
            evaluate_heldout(419, family="invented")

    def test_r420_heldout_background_summary_independent(self):
        report = evaluate_heldout(420, family="background")
        self.assertEqual(report["reachable_states"], report["theoretical_states"])


class DisconnectedCnfTests(unittest.TestCase):
    def _verify(self, seed, components):
        return evaluate_heldout(seed, family="components", components=components)

    def test_r421_single_component_sat(self):
        self.assertFalse(self._verify(421, (False,))["unsatisfiable"])

    def test_r422_single_component_unsat(self):
        self.assertTrue(self._verify(422, (True,))["unsatisfiable"])

    def test_r423_two_sat_components(self):
        self.assertIsNone(self._verify(423, (False, False))["witness"])

    def test_r424_one_late_unsat_component(self):
        self.assertGreater(self._verify(424, (False, True))["proof_clauses"], 0)

    def test_r425_one_early_unsat_component(self):
        self.assertGreater(self._verify(425, (True, False))["proof_clauses"], 0)

    def test_r426_two_unsat_components(self):
        self.assertGreater(self._verify(426, (True, True))["proof_clauses"], 0)

    def test_r427_three_sat_components(self):
        self.assertFalse(self._verify(427, (False, False, False))["unsatisfiable"])

    def test_r428_middle_unsat_of_three(self):
        self.assertTrue(self._verify(428, (False, True, False))["unsatisfiable"])

    def test_r429_last_unsat_of_three(self):
        self.assertTrue(self._verify(429, (False, False, True))["unsatisfiable"])

    def test_r430_first_unsat_of_three(self):
        self.assertTrue(self._verify(430, (True, False, False))["unsatisfiable"])

    def test_r431_all_three_unsat(self):
        self.assertTrue(self._verify(431, (True, True, True))["unsatisfiable"])

    def test_r432_two_nonsat_three_components(self):
        self.assertTrue(self._verify(432, (True, False, True))["unsatisfiable"])

    def test_r433_component_supports_are_disjoint(self):
        _, rows, _ = disconnected_instance(433, contradictory_components=(True, False, True))
        for i in range(3):
            support = {v for row in rows[i * 4:(i + 1) * 4] for v in row.variables}
            self.assertTrue(all((v - 1) // 3 == i for v in support))

    def test_r434_component_count_cap_rejected(self):
        with self.assertRaisesRegex(ValueError, "component cap"):
            disconnected_instance(434, contradictory_components=(True,) * 4)

    def test_r435_empty_component_set_rejected(self):
        with self.assertRaisesRegex(ValueError, "component cap"):
            disconnected_instance(435, contradictory_components=())

    def test_r436_disconnected_witness_from_unsat_component(self):
        _, rows, _ = disconnected_instance(436, contradictory_components=(False, True, False))
        witness, _ = shortest_inconsistent_subset(rows)
        self.assertTrue(all(4 <= i < 8 for i in witness))

    def test_r437_multiple_sources_independently_audited(self):
        f, rows, _ = disconnected_instance(437, contradictory_components=(True, True))
        witness, _ = shortest_inconsistent_subset(rows)
        self.assertTrue(validate_witness_against_original(f, rows, witness)["exact_original_source_verified"])

    def test_r438_seeded_disconnected_sat(self):
        for seed in range(43800, 43808):
            self.assertFalse(self._verify(seed, (False, False, False))["unsatisfiable"])

    def test_r439_seeded_disconnected_unsat(self):
        for seed in range(43900, 43908):
            self.assertTrue(self._verify(seed, (False, True, False))["unsatisfiable"])

    def test_r440_disconnected_state_rank_agreement(self):
        report = self._verify(440, (True, True, False))
        self.assertEqual(report["reachable_states"], report["theoretical_states"])


class IndependentGaussianTests(unittest.TestCase):
    def _rows(self, seed=441, *, contradictory=True):
        return _case(seed, bad=contradictory)[1]

    def test_r441_zero_row_rank(self):
        self.assertEqual(gaussian_dependency_baseline([])["augmented_rank"], 0)

    def test_r442_zero_row_sat(self):
        self.assertFalse(gaussian_dependency_baseline([])["unsatisfiable"])

    def test_r443_single_zero_support_contradiction(self):
        self.assertTrue(gaussian_dependency_baseline([XorEquation([], 1)])["unsatisfiable"])

    def test_r444_single_zero_support_consistent(self):
        self.assertFalse(gaussian_dependency_baseline([XorEquation([], 0)])["unsatisfiable"])

    def test_r445_single_independent_equation_rank(self):
        self.assertEqual(gaussian_dependency_baseline([XorEquation([17], 1)])["coefficient_rank"], 1)

    def test_r446_duplicate_identical_rows_rank(self):
        rows = [XorEquation([1, 3], 0)] * 2
        self.assertEqual(gaussian_dependency_baseline(rows)["augmented_rank"], 1)

    def test_r447_duplicate_opposite_rows_inconsistent(self):
        rows = [XorEquation([1, 3], 0), XorEquation([1, 3], 1)]
        self.assertTrue(gaussian_dependency_baseline(rows)["unsatisfiable"])

    def test_r448_triangle_consistent_rank(self):
        rows = [XorEquation([1, 2], 0), XorEquation([2, 3], 1),
                XorEquation([1, 3], 1)]
        self.assertEqual(gaussian_dependency_baseline(rows)["augmented_rank"], 2)

    def test_r449_triangle_inconsistent_rank(self):
        rows = [XorEquation([1, 2], 0), XorEquation([2, 3], 1),
                XorEquation([1, 3], 0)]
        self.assertEqual(gaussian_dependency_baseline(rows)["augmented_rank"], 3)

    def test_r450_background_sat_rank_equality(self):
        baseline = gaussian_dependency_baseline(self._rows(450, contradictory=False))
        self.assertEqual(baseline["coefficient_rank"], baseline["augmented_rank"])

    def test_r451_background_unsat_rank_gap_one(self):
        baseline = gaussian_dependency_baseline(self._rows(451))
        self.assertEqual(baseline["augmented_rank"], baseline["coefficient_rank"] + 1)

    def test_r452_background_permuted_order_rank(self):
        rows = self._rows(452)
        self.assertEqual(gaussian_dependency_baseline(rows), gaussian_dependency_baseline(list(reversed(rows))))

    def test_r453_variable_renumbering_rank(self):
        rows = self._rows(453)
        shifted = [XorEquation([v + 200 for v in row.variables], row.rhs) for row in rows]
        self.assertEqual(gaussian_dependency_baseline(rows), gaussian_dependency_baseline(shifted))

    def test_r454_consistent_row_duplication_rank(self):
        rows = self._rows(454, contradictory=False)
        self.assertEqual(gaussian_dependency_baseline(rows), gaussian_dependency_baseline(rows + rows[:2]))

    def test_r455_inconsistent_row_duplication_rank(self):
        rows = self._rows(455)
        self.assertEqual(gaussian_dependency_baseline(rows), gaussian_dependency_baseline(rows + rows[:2]))

    def test_r456_augmented_rank_equals_syndrome_state_log(self):
        rows = self._rows(456)
        baseline = gaussian_dependency_baseline(rows)
        self.assertEqual(shortest_inconsistent_subset(rows)[1]["reachable_states"],
                         baseline["theoretical_states"])

    def test_r457_random_signed_matrix_baseline(self):
        rng = random.Random(457)
        for _ in range(64):
            rows = [XorEquation(rng.sample(range(1, 7), rng.randrange(1, 4)), rng.randrange(2))
                    for _ in range(7)]
            baseline = gaussian_dependency_baseline(rows)
            witness, states = shortest_inconsistent_subset(rows)
            self.assertEqual(bool(witness), baseline["unsatisfiable"])
            self.assertEqual(states["reachable_states"], baseline["theoretical_states"])

    def test_r458_variable_cap_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "cap"):
            gaussian_dependency_baseline([XorEquation([1, 2], 0)], max_variables=1)

    def test_r459_twelve_column_bounded_random(self):
        rng = random.Random(459)
        rows = [XorEquation(rng.sample(range(1, 13), 3), rng.randrange(2)) for _ in range(12)]
        baseline = gaussian_dependency_baseline(rows)
        self.assertEqual(shortest_inconsistent_subset(rows)[1]["reachable_states"],
                         baseline["theoretical_states"])

    def test_r460_rank_is_not_general_sat_certificate(self):
        baseline = gaussian_dependency_baseline(self._rows(460))
        self.assertTrue(baseline["unsatisfiable"])
        self.assertNotIn("external_verified", baseline)


@unittest.skipUnless(find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM")),
                     "pinned drat-trim unavailable")
class HeldoutExternalTests(unittest.TestCase):
    def test_r401_r460_independent_original_cnf_checker(self):
        checker = find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM"))
        for seed in range(401000, 401016):
            self.assertTrue(evaluate_heldout(seed, family="background",
                external_checker=checker)["external_verified"])
            self.assertTrue(evaluate_heldout(seed, family="components",
                external_checker=checker)["external_verified"])


class HeldoutNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("native Rust extension absent; CI builds it")

    def test_r401_r460_native_differential(self):
        for seed in range(401000, 401016):
            for family in ("background", "components"):
                self.assertTrue(evaluate_heldout(seed, family=family,
                    compare_rust=True)["native_differential"])


if __name__ == "__main__":
    unittest.main()
