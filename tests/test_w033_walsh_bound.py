"""Independent truth-table checks of the exact W033 spectral certificate."""

import itertools
import random
import unittest

from scripts.w033_walsh_bound import walsh_bound


def min_violated(nvars, clauses):
    return min(sum(not any(assignment[abs(lit)-1] == (lit > 0)
                           for lit in clause) for clause in clauses)
               for assignment in itertools.product((False, True), repeat=nvars))


class TestWalshBound(unittest.TestCase):
    def test_complete_three_variable_cube_certified(self):
        clauses = [tuple(-i if bits[i-1] else i for i in (1, 2, 3))
                   for bits in itertools.product((False, True), repeat=3)]
        result = walsh_bound(3, clauses)
        self.assertEqual(result["status"], "UNSAT_CERTIFIED")
        self.assertEqual(result["constant_numerator"], 8)
        self.assertEqual(result["nonconstant_l1_numerator"], 0)
        self.assertEqual(min_violated(3, clauses), 1)

    def test_mixed_width_complementary_units(self):
        result = walsh_bound(3, [[1], [-1]])
        self.assertEqual(result["status"], "UNSAT_CERTIFIED")
        self.assertEqual(result["lower_bound_numerator"], 8)

    def test_non_xor_implication_chain_certified(self):
        # These original clauses have no triple-width XOR cube at all.
        clauses = [[1], [-1, 2], [-2]]
        result = walsh_bound(2, clauses)
        self.assertEqual(min_violated(2, clauses), 1)
        self.assertEqual(result["status"], "UNSAT_CERTIFIED")
        self.assertEqual(result["lower_bound_numerator"], 4)

    def test_five_variable_thirtyfive_distinct_three_clauses(self):
        # Frozen exploratory witness: no single triple contains every one of
        # its eight polarity patterns (the trivial 3-XOR contradiction cube).
        rng = random.Random(7107)
        pool = [[a * signs[0], b * signs[1], c * signs[2]]
                for a, b, c in itertools.combinations(range(1, 6), 3)
                for signs in itertools.product((-1, 1), repeat=3)]
        for _ in range(13):
            clauses = rng.sample(pool, 35)
        triplet_counts = {}
        for clause in clauses:
            key = tuple(sorted(map(abs, clause)))
            triplet_counts[key] = triplet_counts.get(key, 0) + 1
        self.assertLess(max(triplet_counts.values()), 8)
        result = walsh_bound(5, clauses)
        self.assertEqual(min_violated(5, clauses), 2)
        self.assertEqual(result["lower_bound_numerator"], 2)
        self.assertEqual(result["status"], "UNSAT_CERTIFIED")

    def test_not_every_unsat_is_certified(self):
        clauses = [[1,2], [-1,2], [1,-2], [-1,-2]]
        self.assertEqual(min_violated(2, clauses), 1)
        self.assertEqual(walsh_bound(2, clauses)["status"], "UNSAT_CERTIFIED")
        self.assertEqual(walsh_bound(1, [[1]])["status"], "NO_CERTIFICATE")

    def test_tautology_and_empty_clauses(self):
        self.assertEqual(walsh_bound(2, [[1,-1]])["status"], "NO_CERTIFICATE")
        self.assertEqual(walsh_bound(2, [[]])["status"], "UNSAT_CERTIFIED")

    def test_extra_clauses_can_weaken_global_l1_certificate(self):
        # The original eight-clause cube already proves UNSAT. Adding
        # unrelated clauses preserves UNSAT but can loosen this L1 bound.
        cube = [tuple(-i if bits[i-1] else i for i in (1, 2, 3))
                for bits in itertools.product((False, True), repeat=3)]
        self.assertEqual(walsh_bound(9, cube)["status"], "UNSAT_CERTIFIED")
        augmented = cube + [[4, 5, 6], [7, 8, 9]]
        self.assertEqual(min_violated(9, augmented), 1)
        self.assertEqual(walsh_bound(9, augmented)["status"], "NO_CERTIFICATE")

    def test_random_truth_table_certificate_soundness(self):
        random_source = random.Random(33033)
        for nvars in (1, 2, 3, 4, 5):
            for _ in range(200):
                clauses = [[random_source.choice((-1,1)) * random_source.randrange(1,nvars+1)
                            for _ in range(random_source.randrange(0,4))]
                           for _ in range(random_source.randrange(0,17))]
                # Each clause is independently evaluated by enumerating every assignment.
                result = walsh_bound(nvars, clauses)
                actual = min_violated(nvars, clauses)
                if result["status"] == "UNSAT_CERTIFIED":
                    self.assertGreater(actual, 0)
                # The integer bound itself must hold for every possible assignment.
                self.assertGreaterEqual(actual * result["denominator"],
                                        result["lower_bound_numerator"])


if __name__ == "__main__":
    unittest.main()
