"""Independent planted witness and separator structure checks."""
import unittest

from witnora_core.cnf import formula_satisfied
from witnora_core.hard_separator_families import make_hard_separator_case
from witnora_core.multicut_parity_separator import bounded_parity_separators
from witnora_core.separator_conditioned_solve import primal_components


class HardSeparatorFamilyTests(unittest.TestCase):
    def test_planted_witness_and_cut(self):
        for width in (2, 3):
            for blocks in (2, 4):
                formula, meta = make_hard_separator_case(blocks, 18, width, 2761)
                witness = {v: True for v in formula.variables}
                self.assertTrue(formula_satisfied(formula, witness))
                result = bounded_parity_separators(formula)
                self.assertEqual(result["smallest_cut_size"], width)
                self.assertEqual(len(primal_components(formula, meta["boundary"])),
                                 blocks)

    def test_deterministic_and_bounded(self):
        self.assertEqual(make_hard_separator_case(2, 18, 2, 7),
                         make_hard_separator_case(2, 18, 2, 7))
        with self.assertRaises(ValueError):
            make_hard_separator_case(32, 18, 2, 7)


if __name__ == "__main__":
    unittest.main()
