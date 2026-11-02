"""Proof-obligation-style regression tests for witnessed CNF isomorphism."""
import unittest

from witnora_core.component_equivalence import exact_signed_isomorphism, refined_shape


class ComponentEquivalenceTests(unittest.TestCase):
    def test_permutation_and_sign_flip_witness(self):
        original = [[1, -2, 3], [-1, 2], [2, 3]]
        # Rename 1->9, 2->4, 3->7 and flip polarity on old 2.
        changed = [[9, 4, 7], [-9, -4], [-4, 7]]
        witness = exact_signed_isomorphism(original, changed)
        self.assertIsNotNone(witness)

    def test_refined_shape_preserved_by_witness(self):
        original = [[1, -2, 3], [-1, 2], [2, 3]]
        changed = [[9, 4, 7], [-9, -4], [-4, 7]]
        self.assertEqual(refined_shape(original), refined_shape(changed))

    def test_nonisomorphic_formula_rejected(self):
        left = [[1, 2], [1, -2]]
        right = [[1, 2], [-1, -2]]
        # Both have same simple length count but distinct signed graph shape.
        self.assertIsNone(exact_signed_isomorphism(left, right))

    def test_budget_fails_closed(self):
        rows = [[1, 2, 3, 4, 5, 6, 7]]
        self.assertIsNone(exact_signed_isomorphism(rows, rows))


if __name__ == "__main__":
    unittest.main()
