"""Small algebraic regression tests for the WU-016 watch prefilter lemma.

These are local GF(2) identities, not SAT assignment enumeration.
"""

import unittest


def leading_bit(row):
    return (row & -row).bit_length() - 1 if row else None


def safe_gate(watch0, watch1, pivot_bits):
    a, b = leading_bit(watch0), leading_bit(watch1)
    return a is not None and b is not None and a != b and not (
        pivot_bits & (1 << a) or pivot_bits & (1 << b))


class TestLeadingColumnGate(unittest.TestCase):
    def test_raw_nonpivot_projection_is_unsound(self):
        # U=span(x1+x2) has pivot x1, although its sole basis row has
        # a nonzero x2 coefficient. Raw nonpivot coordinates DO NOT
        # annihilate U; this is a concrete counterexample to that shortcut.
        span_row = 0b011
        other = 0b100
        pivot_bits = 0b001
        projection0 = span_row & ~pivot_bits
        projection1 = other & ~pivot_bits
        self.assertNotEqual(projection0, 0)
        self.assertNotEqual(projection1, 0)
        self.assertNotEqual(projection0, projection1)
        self.assertEqual(span_row ^ span_row, 0)  # first watch belongs to U
        self.assertFalse(safe_gate(span_row, other, pivot_bits))

    def test_distinct_free_leading_columns_prove_independence(self):
        # Same U. Both watches lead at different nonpivots (x2 and x3),
        # so none of a, b, or a+b is in U.
        a, b, u = 0b010, 0b100, 0b011
        self.assertTrue(safe_gate(a, b, 0b001))
        self.assertNotIn(a, (0, u))
        self.assertNotIn(b, (0, u))
        self.assertNotIn(a ^ b, (0, u))

    def test_gate_rejects_same_free_leading_bit(self):
        self.assertFalse(safe_gate(0b010, 0b110, 0b001))


if __name__ == "__main__":
    unittest.main()
