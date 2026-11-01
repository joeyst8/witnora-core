"""Exactness checks for carried clause-mask simplification and components."""
import unittest

from scripts.experiment_inloop_masked_state import (
    clauses_with_masks, simplify_masked, components_masked,
)
from scripts.benchmark_separator_decomposition import simplify, components


class MaskedStateTests(unittest.TestCase):
    def test_masked_simplify_matches_literal_simplification(self):
        rows = [[1, -2, 3], [-1, 4], [2, 5], [-3, -4, 6]]
        for assignment in ({1: True}, {2: False}, {3: True, 4: False}):
            expected = simplify(rows, assignment)
            actual = simplify_masked(clauses_with_masks(rows), assignment)
            self.assertEqual(
                expected, None if actual is None else [list(r) for r, _ in actual])

    def test_masked_components_match_primal_graph(self):
        rows = [[1, 2], [2, 3], [5, 6], [8], [8, 9]]
        original = components(rows)
        masked = components_masked(clauses_with_masks(rows))
        normalize = lambda groups: sorted(
            sorted(tuple(sorted(row)) for row in group) for group in groups)
        self.assertEqual(
            normalize(original),
            normalize([[list(row) for row, _ in group] for group in masked]))


if __name__ == "__main__":
    unittest.main()
