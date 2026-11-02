"""Independent exhaustive truth-table checks of the exact symbolic gate."""
import itertools
import unittest

from scripts.experiment_satlib_symbolic_syndrome_bdd import (
    SyndromeBDD, add_bdd_acceptance_gate, benchmark, sparse_side_syndromes,
    symbolic_side_syndromes,
)


class SymbolicSyndromeBDDTests(unittest.TestCase):
    def test_cnf_gate_matches_exact_bdd_for_all_indicator_inputs(self):
        from pycryptosat import Solver
        for mask in (0, 1, 7, 31, 85, 170, 240, 255):
            bdd = SyndromeBDD(width=3)
            root = 0
            for value in range(8):
                if mask & (1 << value):
                    root = bdd.union(root, bdd.xor_translate(bdd.zero_vector, value))
            for shift in range(8):
                solver = Solver(threads=1)
                for indicator in (1, 2, 3):
                    solver.add_clause([indicator, -indicator])
                add_bdd_acceptance_gate(solver, bdd, root, (1, 2, 3), shift)
                for signature in range(8):
                    assumptions = [v if signature & (1 << (v - 1)) else -v
                                   for v in (1, 2, 3)]
                    sat, _ = solver.solve(assumptions=assumptions)
                    self.assertEqual(sat, bdd.contains(root, signature ^ shift))

    def test_exact_bdd_intersection_and_witness(self):
        for a in range(0, 256, 11):
            for b in range(0, 256, 13):
                bdd = SyndromeBDD(width=3)
                roots = []
                for mask in (a, b):
                    root = 0
                    for value in range(8):
                        if mask & (1 << value):
                            root = bdd.union(root, bdd.xor_translate(bdd.zero_vector,
                                                                      value))
                    roots.append(root)
                intersection = bdd.intersect(*roots)
                expected = {value for value in range(8) if (a & b) & (1 << value)}
                self.assertEqual(bdd.cardinality(intersection), len(expected))
                self.assertEqual({value for value in range(8)
                                  if bdd.contains(intersection, value)}, expected)
                chosen = bdd.choose_member(intersection)
                self.assertEqual(chosen is None, not bool(expected))
                if chosen is not None:
                    self.assertIn(chosen, expected)

    def test_xor_translate_union_and_membership_over_all_small_subsets(self):
        for mask in range(1 << 8):
            bdd = SyndromeBDD(width=3)
            root = 0
            for value in range(8):
                if mask & (1 << value):
                    root = bdd.union(root, bdd.xor_translate(bdd.zero_vector, value))
            for shift in range(8):
                shifted = bdd.xor_translate(root, shift)
                self.assertEqual(bdd.cardinality(shifted), mask.bit_count())
                for signature in range(8):
                    self.assertEqual(bdd.contains(shifted, signature),
                                     bool(mask & (1 << (signature ^ shift))))

    def test_frontier_dp_matches_bruteforce_with_boundary_cnf_and_xor(self):
        split = {"boundary": (1,), "right_vars": (1, 2, 3, 4, 5),
                 "right_clauses": [(1, -2, 3), (-3, 4), (-4, 5)],
                 "right_xors": [((1, 2, 4), 1), ((2, 3, 5), 0)]}
        columns = {2: 3, 3: 5, 4: 6, 5: 1}
        for boundary_bits in (0, 1):
            bdd, root, stats = symbolic_side_syndromes(
                split, "right", boundary_bits, columns, width=3)
            expected = []
            for bits in itertools.product((False, True), repeat=4):
                assignment = {1: bool(boundary_bits)}
                assignment.update(zip((2, 3, 4, 5), bits))
                clauses_hold = all(any(assignment[abs(l)] == (l > 0) for l in clause)
                                   for clause in split["right_clauses"])
                xors_hold = all((sum(assignment[v] for v in support) & 1) == rhs
                                for support, rhs in split["right_xors"])
                if clauses_hold and xors_hold:
                    signature = 0
                    for v in (2, 3, 4, 5):
                        if assignment[v]:
                            signature ^= columns[v]
                    expected.append(signature)
            self.assertEqual(stats["models"], len(expected))
            self.assertEqual({s for s in range(8) if bdd.contains(root, s)},
                             set(expected))
            self.assertLessEqual(stats["frontier_width_peak"], 4)

    def test_sparse_frontier_tracks_exact_models_syndromes_and_witnesses(self):
        split = {"boundary": (1,), "left_vars": (1, 2, 3, 4, 5),
                 "left_clauses": [(1, -2, 3), (-3, 4), (-4, 5)],
                 "left_xors": [((1, 2, 4), 1), ((2, 3, 5), 0)]}
        columns = {2: 3, 3: 5, 4: 6, 5: 1}
        for boundary_bits in (0, 1):
            signatures, stats = sparse_side_syndromes(
                split, "left", boundary_bits, columns)
            expected = []
            for bits in itertools.product((False, True), repeat=4):
                assignment = {1: bool(boundary_bits)}
                assignment.update(zip((2, 3, 4, 5), bits))
                if all(any(assignment[abs(l)] == (l > 0) for l in clause)
                       for clause in split["left_clauses"]) and all(
                       (sum(assignment[v] for v in support) & 1) == rhs
                       for support, rhs in split["left_xors"]):
                    sig = 0
                    for v in (2, 3, 4, 5):
                        if assignment[v]:
                            sig ^= columns[v]
                    expected.append(sig)
            self.assertEqual(stats["models"], len(expected))
            self.assertEqual(set(signatures), set(expected))
            for sig, witness in signatures.items():
                assignment = {1: bool(boundary_bits)}
                assignment.update({v: bool(witness & (1 << (v - 1)))
                                   for v in (2, 3, 4, 5)})
                self.assertTrue(all(any(assignment[abs(l)] == (l > 0)
                                        for l in clause) for clause in split["left_clauses"]))
                self.assertTrue(all((sum(assignment[v] for v in support) & 1) == rhs
                                    for support, rhs in split["left_xors"]))
                self.assertEqual(sig, 0 ^ (columns[2] if assignment[2] else 0)
                                 ^ (columns[3] if assignment[3] else 0)
                                 ^ (columns[4] if assignment[4] else 0)
                                 ^ (columns[5] if assignment[5] else 0))

    def test_two_sided_symbolic_xor_join_is_exact(self):
        split = {"boundary": (1,), "left_vars": (1, 2, 3),
                 "right_vars": (1, 4, 5),
                 "left_clauses": [(1, 2), (-2, 3)],
                 "right_clauses": [(-1, 4), (-4, 5)],
                 "left_xors": [((1, 2, 3), 1)],
                 "right_xors": [((1, 4, 5), 0)]}
        columns = {2: 1, 3: 3, 4: 4, 5: 6}
        for boundary_bits in (0, 1):
            bdd = SyndromeBDD(width=3)
            _, left, left_stats = symbolic_side_syndromes(
                split, "left", boundary_bits, columns, width=3, bdd=bdd)
            _, right, right_stats = symbolic_side_syndromes(
                split, "right", boundary_bits, columns, width=3, bdd=bdd)
            self.assertGreaterEqual(left_stats["models"], 0)
            self.assertGreaterEqual(right_stats["models"], 0)
            for required in range(8):
                joined = bdd.intersect(left, bdd.xor_translate(right, required))
                possible = any(bdd.contains(left, ls) and
                               bdd.contains(right, ls ^ required)
                               for ls in range(8))
                self.assertEqual(bdd.choose_member(joined) is not None, possible)

    def test_boundary_only_unsat_is_exact_empty_set(self):
        split = {"boundary": (1,), "right_vars": (1, 2),
                 "right_clauses": [(1,)], "right_xors": []}
        bdd, root, stats = symbolic_side_syndromes(split, "right", 0,
                                                   {2: 1}, width=2)
        self.assertEqual((root, stats["models"]), (0, 0))
        self.assertFalse(any(bdd.contains(root, x) for x in range(4)))

    def test_holdout_rejected_before_source_fetch(self):
        with self.assertRaises(ValueError):
            benchmark("par32-2-c.cnf.Z")


if __name__ == "__main__":
    unittest.main()
