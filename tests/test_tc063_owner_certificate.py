"""TC-063 owner-certificate regression and finite semantic tests."""

import random
import unittest
from itertools import product

from witnora_core.tc063_owner_certificate import (
    condition_verified_partition,
    verify_owner_partition,
)


def component(cid, variables, clauses, boundary):
    return {
        "component_id": cid,
        "variables": variables,
        "clause_ids": clauses,
        "boundary_separator_variables": boundary,
    }


def satisfies(clauses, assignment):
    return all(
        any(assignment[abs(lit)] == (lit > 0) for lit in clause)
        for clause in clauses
    )


class OwnerCertificateTests(unittest.TestCase):
    def test_raw_occurrences_not_discarded(self):
        formula = [[1, 2], [1, 2], [-1, 3], [1, -1], [-1], []]
        parts = [
            component("A", [2], [1, 2], [1]),
            component("B", [3], [3], [1]),
        ]
        check = verify_owner_partition(formula, [1], parts)
        self.assertTrue(check["accepted"], check)
        self.assertEqual(check["separator_only_clause_ids"], [4, 5, 6])
        self.assertEqual(check["owner_by_clause_id"], {"1": "A", "2": "A", "3": "B"})

    def test_cross_component_and_owner_tamper_rejected(self):
        formula = [[1, 2], [-1, 3], [2, 3]]
        parts = [component("A", [2], [1], [1]), component("B", [3], [2], [1])]
        check = verify_owner_partition(formula, [1], parts)
        self.assertFalse(check["accepted"])
        self.assertTrue(any("CROSS_COMPONENT" in e for e in check["errors"]))

        formula = [[1, 2], [-1, 3]]
        parts = [component("A", [2], [1, 2], [1]), component("B", [3], [], [1])]
        self.assertFalse(verify_owner_partition(formula, [1], parts)["accepted"])

    def test_duplicate_clause_id_and_missing_variable_rejected(self):
        formula = [[1, 2]]
        self.assertFalse(
            verify_owner_partition(
                formula, [1], [component("A", [2], [1, 1], [1])]
            )["accepted"]
        )
        self.assertFalse(verify_owner_partition(formula, [1], [])["accepted"])

    def test_separator_only_empty_clause_is_not_lost(self):
        formula = [[1], [-1], []]
        check = verify_owner_partition(formula, [1], [])
        self.assertTrue(check["accepted"])
        self.assertEqual(check["separator_only_clause_ids"], [1, 2, 3])
        conditioned = condition_verified_partition(formula, [1], [], {1: True})
        self.assertEqual(conditioned["separator_residual"], [[], []])

    def test_randomized_equivalence_with_all_assignments(self):
        rng = random.Random(63063)
        compared = 0
        for _ in range(800):
            n = rng.randrange(1, 8)
            clauses = [
                [rng.choice([-1, 1]) * rng.randint(1, n)
                 for _ in range(rng.randrange(0, 5))]
                for _ in range(rng.randrange(1, 12))
            ]
            if rng.random() < 0.3:
                clauses.append(list(clauses[0]))
            variables = {abs(lit) for clause in clauses for lit in clause}
            separator = sorted(v for v in variables if rng.random() < 0.3)
            local = sorted(variables - set(separator))
            components = []
            if local:
                ids = [
                    i for i, clause in enumerate(clauses, 1)
                    if any(abs(lit) in local for lit in clause)
                ]
                boundary = sorted({
                    abs(lit) for i in ids for lit in clauses[i - 1]
                    if abs(lit) in separator
                })
                components = [component("C1", local, ids, boundary)]
            check = verify_owner_partition(clauses, separator, components)
            self.assertTrue(check["accepted"], (clauses, separator, check))
            for bits in product([False, True], repeat=n):
                assignment = {i + 1: bits[i] for i in range(n)}
                fixed = {var: assignment[var] for var in separator}
                residual = condition_verified_partition(
                    clauses, separator, components, fixed
                )
                all_buckets = [
                    residual["separator_residual"],
                    *residual["component_residuals"].values(),
                ]
                self.assertEqual(
                    satisfies(clauses, assignment),
                    all(satisfies(bucket, assignment) for bucket in all_buckets),
                )
                compared += 1
        self.assertGreater(compared, 25000)


if __name__ == "__main__":
    unittest.main()
