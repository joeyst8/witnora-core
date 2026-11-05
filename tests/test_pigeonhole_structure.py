import unittest

from witnora_core.collapse_theory import (
    PIGEONHOLE_STRUCTURE_RECOGNIZED,
    _pigeonhole_formula,
    recognize_pigeonhole_structure,
)


class PigeonholeStructureTest(unittest.TestCase):
    def test_pigeonhole_grid_recognition(self):
        structure = recognize_pigeonhole_structure(_pigeonhole_formula(3, 2), instance_id="php_3_2")
        self.assertEqual(structure.assignment_variables[0], {"pigeon": 1, "hole": 1, "variable": 1})
        self.assertEqual(structure.assignment_variables[-1], {"pigeon": 3, "hole": 2, "variable": 6})
        print("PIGEONHOLE_GRID_RECOGNITION_PASS")

    def test_pigeonhole_structure_recognition(self):
        structure = recognize_pigeonhole_structure(_pigeonhole_formula(5, 4), instance_id="php_5_4")
        self.assertEqual(structure.status, PIGEONHOLE_STRUCTURE_RECOGNIZED)
        self.assertTrue(structure.recognized_from_original_cnf)
        self.assertTrue(structure.exact_structure)
        print("PIGEONHOLE_STRUCTURE_RECOGNITION_PASS")

    def test_pigeonhole_n_gt_m(self):
        structure = recognize_pigeonhole_structure(_pigeonhole_formula(6, 5), instance_id="php_6_5")
        self.assertTrue(structure.n_greater_than_m)
        print("PIGEONHOLE_N_GT_M_PASS")

    def test_pigeonhole_n_le_m_no_contradiction(self):
        structure = recognize_pigeonhole_structure(_pigeonhole_formula(2, 2), instance_id="php_2_2")
        self.assertTrue(structure.exact_structure)
        self.assertFalse(structure.n_greater_than_m)
        print("PIGEONHOLE_N_LE_M_NO_CONTRADICTION_PASS")


if __name__ == "__main__":
    unittest.main()
