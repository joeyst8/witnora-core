"""WU-017 GF(2) quotient signature regressions (not SAT search)."""

import unittest


def reduce_canonically(value, rows):
    """Use pivot-sorted echelon rows to remove all pivot bits."""
    for pivot, basis_row in rows:
        if value & (1 << pivot):
            value ^= basis_row
    return value


def signature(remainder, free_columns, width):
    return sum(((remainder >> bit) & 1) << out
               for out, bit in enumerate(free_columns[:width]))


def proves_independent(a, b):
    return a != 0 and b != 0 and a != b


class TestQuotientSignatures(unittest.TestCase):
    def test_canonical_reduction_fixes_unsound_raw_projection(self):
        rows = [(0, 0b011)]
        free = (1, 2)
        a, b = 0b011, 0b100
        raw_a = signature(a, free, 2)
        raw_b = signature(b, free, 2)
        self.assertTrue(proves_independent(raw_a, raw_b))  # UNSOUND raw projection
        a_reduced = reduce_canonically(a, rows)
        b_reduced = reduce_canonically(b, rows)
        self.assertFalse(proves_independent(signature(a_reduced, free, 2),
                                            signature(b_reduced, free, 2)))

    def test_distinct_nonzero_signatures_are_valid_witnesses(self):
        rows = [(0, 0b011)]
        free = (1, 2)
        a, b = reduce_canonically(0b010, rows), reduce_canonically(0b100, rows)
        self.assertTrue(proves_independent(signature(a, free, 2), signature(b, free, 2)))
        self.assertTrue(proves_independent(a, b))

    def test_prefix_can_fail_to_certify_independent_pair(self):
        # For U=0 and three free columns, two witnesses can be independent
        # even though a narrow one-bit prefix cannot distinguish them.
        a, b = 0b010, 0b100
        free = (0, 1, 2)
        self.assertFalse(proves_independent(signature(a, free, 1),
                                            signature(b, free, 1)))
        self.assertTrue(proves_independent(a, b))


if __name__ == "__main__":
    unittest.main()
