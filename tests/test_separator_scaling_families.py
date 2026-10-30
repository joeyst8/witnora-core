"""Deterministic family and full-CNF separator controls."""
import unittest

from witnora_core.separator_scaling_families import make_scaling_case
from witnora_core.multicut_parity_separator import bounded_parity_separators
from witnora_core.separator_conditioned_solve import primal_components, solve_conditioned


class ScalingFamilyTests(unittest.TestCase):
    def test_expected_cut_and_satisfiability(self):
        for width in (2, 3):
            for blocks in (1, 2, 4):
                source, meta = make_scaling_case(blocks, width)
                found = bounded_parity_separators(source)
                self.assertEqual(found["smallest_cut_size"], width)
                self.assertIn(list(meta["expected_boundary"]),
                              [c["variables"] for c in found["candidate_cuts"]])
                self.assertEqual(len(primal_components(source, meta["expected_boundary"])),
                                 2 * blocks)
                result = solve_conditioned(source)
                self.assertTrue(result["satisfiable"])
                self.assertEqual(result["mode"], "conditioned")

    def test_deterministic_and_bounded(self):
        self.assertEqual(make_scaling_case(3, 2), make_scaling_case(3, 2))
        with self.assertRaises(ValueError):
            make_scaling_case(129, 2)


if __name__ == "__main__":
    unittest.main()
