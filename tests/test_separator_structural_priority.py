"""Independent checks for the TC-063 articulation-first separator prototype."""

import random
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.separator_structural_priority import (
    articulation_vertices,
    prioritized_singletons,
)
from witnora_core.separator_affine_family_theorem import (
    SEPARATOR_AFFINE_FAMILY_RECOGNIZED,
    make_separator_affine_instance,
    recognize_separator_affine_family,
)


def component_count(graph, removed=None):
    remaining = set(graph)
    remaining.discard(removed)
    seen = set()
    count = 0
    for root in sorted(remaining):
        if root in seen:
            continue
        count += 1
        stack = [root]
        seen.add(root)
        while stack:
            for neighbor in graph[stack.pop()] & remaining:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
    return count


class StructuralSeparatorPriorityTest(unittest.TestCase):
    def test_iterative_articulations_match_independent_removal_oracle(self):
        rng = random.Random(63063)
        for n in range(1, 10):
            for _ in range(75):
                graph = {v: set() for v in range(1, n + 1)}
                for left in graph:
                    for right in range(left + 1, n + 1):
                        if rng.random() < 0.3:
                            graph[left].add(right)
                            graph[right].add(left)
                base = component_count(graph)
                expected = tuple(
                    v for v in graph if component_count(graph, v) > base
                )
                self.assertEqual(articulation_vertices(graph), expected)
                ranked = prioritized_singletons(graph)
                self.assertEqual(set(ranked), set(graph))
                self.assertEqual(len(ranked), len(graph))

    def test_long_path_avoids_recursion_depth(self):
        n = 2000
        graph = {
            v: set(range(max(1, v - 1), min(n, v + 1) + 1)) - {v}
            for v in range(1, n + 1)
        }
        cuts = articulation_vertices(graph)
        self.assertEqual(len(cuts), n - 2)
        self.assertEqual(cuts[0], 2)
        self.assertEqual(cuts[-1], n - 1)

    def test_structural_priority_finds_relabelled_tc063_separator_first(self):
        instance = make_separator_affine_instance("saf_sat_chain_4")
        original = instance.formula.variables
        new_separator = max(original) + 100
        raw = [
            [
                (1 if literal > 0 else -1)
                * (new_separator if abs(literal) == 1 else abs(literal))
                for literal in clause
            ]
            for clause in instance.formula.clauses
        ]
        renamed = CNFFormula.from_raw_clauses(raw)
        structural = recognize_separator_affine_family(
            renamed, c=1, r=2, priority="structural"
        )
        baseline = recognize_separator_affine_family(
            renamed, c=1, r=2, priority="lexicographic"
        )
        self.assertEqual(structural["status"], SEPARATOR_AFFINE_FAMILY_RECOGNIZED)
        self.assertEqual(baseline["status"], structural["status"])
        self.assertEqual(structural["separator_variables"], [new_separator])
        self.assertEqual(baseline["separator_variables"], [new_separator])
        self.assertEqual(structural["candidates_examined"], 1)
        self.assertGreater(baseline["candidates_examined"], 1)
        self.assertEqual(structural["trace"][0]["separator"], [new_separator])

    def test_rejection_is_not_overridden_by_structural_hint(self):
        # A three-variable clique has no singleton primal separator.
        # A fixture invalid for one *specified* separator could still have
        # another valid separator, so it is not a universal negative.
        formula = CNFFormula.from_raw_clauses([[1, 2, 3]])
        structural = recognize_separator_affine_family(
            formula, c=1, r=2, priority="structural"
        )
        baseline = recognize_separator_affine_family(
            formula, c=1, r=2, priority="lexicographic"
        )
        self.assertEqual(structural["status"], baseline["status"])
        self.assertNotEqual(structural["status"], SEPARATOR_AFFINE_FAMILY_RECOGNIZED)

    def test_invalid_priority_rejected(self):
        instance = make_separator_affine_instance("saf_sat_chain_2")
        with self.assertRaises(ValueError):
            recognize_separator_affine_family(instance.formula, priority="unchecked")


if __name__ == "__main__":
    unittest.main()
