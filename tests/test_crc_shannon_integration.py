"""Source-level weighted Shannon fallback controls for overlapping CNF."""
import itertools
import random
import unittest

from witnora_core.crc_boundary import count_asymmetric_boundary
from witnora_core.crc_source import count_signed_cnf_crc


def independent_count(clauses, nvars):
    result = 0
    for assignment in itertools.product((False, True), repeat=nvars):
        if all(any(assignment[abs(lit)-1] == (lit > 0) for lit in clause)
               for clause in clauses):
            result += 1
    return result


def dense_control(seed, nvars, nclauses):
    rng = random.Random(seed)
    return tuple(
        tuple(v if rng.randrange(2) else -v
              for v in rng.sample(range(1, nvars + 1), 3))
        for _ in range(nclauses)
    )


class TestCRCShannonIntegration(unittest.TestCase):
    def test_random_original_cnf_fallback(self):
        rng = random.Random(61203)
        used_shannon = 0
        for _ in range(200):
            n = rng.randrange(1, 9)
            clauses = tuple(
                tuple(rng.choice((-1, 1)) * rng.randrange(1, n+1)
                      for _ in range(rng.randrange(1, 5)))
                for _ in range(rng.randrange(2, 19))
            )
            got = count_signed_cnf_crc(
                clauses, n, max_inclusion_subsets=1,
                max_coefficient_states=10_000,
            )
            self.assertIsNotNone(got)
            self.assertEqual(got.models, independent_count(clauses, n))
            used_shannon += (got.coefficient_stats.coefficient_backend == "shannon")
        self.assertGreater(used_shannon, 150)

    def test_dense_controls_previous_ie_budget_failures(self):
        for n, m, seed in ((10, 42, 20261103), (12, 51, 20261104)):
            source = dense_control(seed, n, m)
            result = count_signed_cnf_crc(
                source, n, max_inclusion_subsets=1024,
                max_coefficient_states=4000,
            )
            self.assertIsNotNone(result)
            self.assertEqual(result.models, independent_count(source, n))
            self.assertEqual(result.coefficient_stats.coefficient_backend, "shannon")
            self.assertLessEqual(result.coefficient_stats.coefficient_states, 4000)

    def test_two_selected_modes_through_overlapping_cnf(self):
        b = tuple(range(1, 9))
        source = dense_control(61100, 8, 16)
        even_parity = (1 << 8) - 1
        got = count_asymmetric_boundary(
            ((even_parity, 0),), (), b, source,
            max_inclusion_subsets=1, max_coefficient_states=4000,
        )
        self.assertIsNotNone(got)
        expected = 0
        for bits in range(1 << 8):
            if bits.bit_count() % 2:
                continue
            if all(any(bool(bits & (1 << (abs(lit)-1))) == (lit > 0)
                       for lit in c) for c in source):
                expected += 1
        self.assertEqual(got.models, expected)
        self.assertEqual(got.coefficient_queries, 2)
        self.assertEqual(got.coefficient_backend, "shannon")

    def test_state_budget_failure_preserves_incomplete(self):
        source = dense_control(61001, 12, 40)
        self.assertIsNone(count_signed_cnf_crc(
            source, 12, max_inclusion_subsets=1,
            max_coefficient_states=1,
        ))


if __name__ == "__main__":
    unittest.main()
