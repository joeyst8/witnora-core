"""Independent exhaustive reference for Python spoke discovery completeness.

This is bounded differential evidence, not a proof of all CPython executions.
The reference enumerates every endpoint/intermediate combination and all
16 parity labels, without using the optimized graph detector's data flow.
"""
from itertools import combinations, product
import random
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.spoke_discovery import (discover_parity_spoke_conflicts,
                                         extract_binary_xor_equations, extract_spoke_paths)
from witnora_core.xor import canonical_xor_cnf_clauses


def reference(formula):
    clauses = set(map(tuple, formula.to_clause_lists()))
    ids = sorted(formula.variables)
    found = set()
    for x, z in combinations(ids, 2):
        for m, n in combinations((v for v in ids if v not in (x, z)), 2):
            for l, r, l2, r2 in product((0, 1), repeat=4):
                if (l ^ r) == (l2 ^ r2):
                    continue
                patterns = (
                    canonical_xor_cnf_clauses((x, m), l),
                    canonical_xor_cnf_clauses((m, z), r),
                    canonical_xor_cnf_clauses((x, n), l2),
                    canonical_xor_cnf_clauses((n, z), r2),
                )
                if all(pattern.issubset(clauses) for pattern in patterns):
                    found.add((x, z, m, l, r, n, l2, r2))
    return found


def detected(formula):
    output = set()
    for candidate in discover_parity_spoke_conflicts(formula):
        x, z = candidate["endpoints"]
        first, second = candidate["paths"]
        def parts(path):
            middle = path["middle"]
            eq = {frozenset(e["variables"]): e["rhs"] for e in path["equations"]}
            return middle, eq[frozenset((x, middle))], eq[frozenset((middle, z))]
        m, l, r = parts(first)
        n, l2, r2 = parts(second)
        if m > n:
            m, n, l, r, l2, r2 = n, m, l2, r2, l, r
        output.add((x, z, m, l, r, n, l2, r2))
    return output


def binary_reference(formula):
    clauses = set(map(tuple, formula.to_clause_lists()))
    return [
        (u, v, rhs)
        for u, v in combinations(sorted(formula.variables), 2)
        for rhs in (0, 1)
        if canonical_xor_cnf_clauses((u, v), rhs).issubset(clauses)
    ]



def path_reference(formula):
    clauses = set(map(tuple, formula.to_clause_lists()))
    ids = sorted(formula.variables)
    return [
        (x, z, middle, left, right)
        for x, z in combinations(ids, 2)
        for middle in ids
        if middle not in (x, z)
        for left, right in product((0, 1), repeat=2)
        if canonical_xor_cnf_clauses((x, middle), left).issubset(clauses)
        and canonical_xor_cnf_clauses((middle, z), right).issubset(clauses)
    ]


class SpokeDiscoveryReferenceTest(unittest.TestCase):
    def test_randomized_complete_enumeration(self):
        rng = random.Random(100901)
        for _ in range(70):
            clauses = set()
            for _ in range(rng.randint(4, 15)):
                u, v = sorted(rng.sample(range(1, 6), 2))
                rhs = rng.randrange(2)
                clauses.update(canonical_xor_cnf_clauses((u, v), rhs))
                if rng.random() < 0.22:
                    clauses.add((u, v, -u))
            formula = CNFFormula.from_raw_clauses(clauses)
            self.assertEqual(detected(formula), reference(formula))
            self.assertEqual(extract_binary_xor_equations(formula), binary_reference(formula))
            self.assertEqual(extract_spoke_paths(formula), path_reference(formula))

    def test_handbuilt_conflict_and_missing_clause(self):
        clauses = set()
        for u, v, rhs in ((1, 3, 0), (3, 2, 0), (1, 4, 0), (4, 2, 1)):
            clauses.update(canonical_xor_cnf_clauses((u, v), rhs))
        formula = CNFFormula.from_raw_clauses(clauses)
        self.assertTrue(reference(formula))
        self.assertEqual(detected(formula), reference(formula))
        for missing in sorted(clauses):
            smaller = CNFFormula.from_raw_clauses(clauses - {missing})
            self.assertEqual(detected(smaller), reference(smaller))
            self.assertEqual(extract_spoke_paths(smaller), path_reference(smaller))


if __name__ == "__main__":
    unittest.main()
