"""W-CRC-012 cutset model counting versus independent brute #SAT."""
from __future__ import annotations

import random
import unittest

from witnora_core.crc_cutset_count import count_source_by_separator


def brute_models(clauses, n):
    return sum(
        all(any(bool(mask & (1 << (abs(lit) - 1))) == (lit > 0)
                for lit in clause) for clause in clauses)
        for mask in range(1 << n)
    )


class TestCutsetModelCount(unittest.TestCase):
    def test_star_formula_exact_closed_form(self):
        for n in (6, 8, 12):
            source = [[v, n] for v in range(1, n)]
            result = count_source_by_separator(
                source, tuple(range(1, n + 1)),
                (1,), (2,), (1 << n) - 1)
            self.assertIsNotNone(result)
            self.assertEqual(result.separator, (n,))
            self.assertEqual(result.models, (1 << (n - 1)) + 1)
            self.assertEqual(result.separator_branches, 2)
            if n <= 8:
                self.assertEqual(result.models, brute_models(source, n))

    def test_xor_equivalence_chain_counts_two(self):
        source = [[-1, 2], [1, -2], [-2, 3], [2, -3]]
        result = count_source_by_separator(
            source, (1, 2, 3), (1,), (3,), 7)
        self.assertEqual(result.models, 2)
        self.assertEqual(result.separator, (2,))

    def test_disconnected_zero_separator_product(self):
        source = [[1, 3], [2, 4]]
        result = count_source_by_separator(
            source, (1, 2, 3, 4), (1,), (2,), 15,
            max_separator_size=0)
        self.assertEqual(result.models, 9)
        self.assertEqual(result.separator, ())

    def test_two_hub_separator_and_unsat_conditioning_branch(self):
        source = [[1, 5], [5, 3], [1, 6], [6, 3]]
        result = count_source_by_separator(
            source, (1, 2, 3, 4, 5, 6), (1,), (3,), 63,
            max_separator_size=2)
        self.assertEqual(result.models, brute_models(source, 6))
        self.assertEqual(result.separator, (5, 6))
        # Branch S=0 can violate the following unit clause.
        source.append([5])
        again = count_source_by_separator(
            source, (1, 2, 3, 4, 5, 6), (1,), (3,), 63,
            max_separator_size=2)
        self.assertEqual(again.models, brute_models(source, 6))

    def test_rejects_large_component_or_unverified_witness(self):
        source = [[1, 3], [3, 4], [4, 5], [5, 2]]
        self.assertIsNone(count_source_by_separator(
            source, (1, 2, 3, 4, 5), (1,), (2,), 31,
            max_component_variables=1))
        self.assertIsNone(count_source_by_separator(
            [[1]], (1, 2), (1,), (2,), 0))
        self.assertIsNone(count_source_by_separator(
            [[1, 2]], (1, 2), (1,), (2,), 3))
        self.assertIsNone(count_source_by_separator(
            [[1, 3], [3, 2]], (1, 2, 3), (1,), (2,), 7,
            max_separator_branches=1))
        with self.assertRaises(ValueError):
            count_source_by_separator(
                source, (1, 2, 3, 4, 5), (1,), (2,), 31,
                max_assignment_states=0)

    def test_120_random_exact_differentials(self):
        rng = random.Random(12012)
        admitted = 0
        for n in (6, 7, 8):
            boundary = tuple(range(1, n + 1))
            for _ in range(40):
                source = []
                for _ in range(rng.randrange(0, 10)):
                    vars = rng.sample(boundary, rng.randrange(1, 4))
                    signed = [v if rng.randrange(2) else -v for v in vars]
                    signed[0] = vars[0]  # all-ones witness
                    source.append(signed)
                result = count_source_by_separator(
                    source, boundary, (1,), (2,), (1 << n) - 1,
                    max_separator_size=2, max_component_variables=8)
                if result is None:
                    continue
                self.assertEqual(result.models, brute_models(source, n))
                admitted += 1
        self.assertGreater(admitted, 10)


if __name__ == "__main__":
    unittest.main()
