import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.collapse_theory import (
    CARDINALITY_STRUCTURE_DETECTED,
    _pigeonhole_formula,
    detect_cardinality_pb,
    recognize_pigeonhole_structure,
)


class CardinalityDetectionTest(unittest.TestCase):
    def test_cardinality_amo_detection(self):
        structure = recognize_pigeonhole_structure(_pigeonhole_formula(3, 2), instance_id="php_3_2")
        self.assertTrue(structure.exact_structure)
        self.assertFalse(structure.missing_amo_pairs)
        self.assertEqual(sum(len(rows) for rows in structure.amo_by_hole.values()), 6)
        print("CARDINALITY_AMO_DETECTION_PASS")

    def test_cardinality_alo_detection(self):
        structure = recognize_pigeonhole_structure(_pigeonhole_formula(4, 3), instance_id="php_4_3")
        self.assertEqual(len(structure.alo_by_pigeon), 4)
        self.assertFalse(structure.missing_alo)
        print("CARDINALITY_ALO_DETECTION_PASS")

    def test_cardinality_exact_one(self):
        formula = CNFFormula.from_raw_clauses([[1, 2, 3], [-1, -2], [-1, -3], [-2, -3]])
        result = detect_cardinality_pb(formula)
        self.assertEqual(result["status"], CARDINALITY_STRUCTURE_DETECTED)
        self.assertEqual(result["exactly_one_constraints"], [[1, 2, 3]])
        print("CARDINALITY_EXACT_ONE_PASS")

    def test_cardinality_incomplete_reject(self):
        formula = _pigeonhole_formula(3, 2)
        removed = []
        skipped = False
        for clause in formula.clauses:
            if not skipped and clause.literals == (-3, -1):
                skipped = True
                continue
            removed.append(clause.to_list())
        incomplete = CNFFormula.from_raw_clauses(removed)
        structure = recognize_pigeonhole_structure(incomplete, instance_id="php_3_2")
        self.assertFalse(structure.exact_structure)
        self.assertTrue(structure.missing_amo_pairs)
        print("CARDINALITY_INCOMPLETE_REJECT_PASS")


if __name__ == "__main__":
    unittest.main()
