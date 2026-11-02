"""Independent fixture checks for the concrete two-component G14 bridge.

These tests audit graph ownership and literal replacement. The Lean kernel,
not this Python file, checks the claimed logical implication.
"""

import itertools
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "theory" / "Dubois20SourceUnsat.lean").read_text()
BRIDGE = (ROOT / "theory" / "TC063DuboisTwoComponentCover.lean").read_text()
CERT = json.loads((ROOT / "research" / "PR119_DUBOIS20_SOURCE_XOR_CERTIFICATE.json").read_text())
EQS = CERT["proof_equations"]
A = tuple(range(10)) + tuple(range(30, 40))
B = tuple(range(10, 30))
SEPARATOR = {10, 29}


def body(text: str, name: str) -> str:
    match = re.search(
        rf"(?ms)^def {name} \([^\n]*\) : (?:Bool|Prop) :=\n(.*?)(?=\n(?:def |theorem |private theorem |-- |end |#print ))",
        text,
    )
    if match is None:
        raise AssertionError(f"Missing definition {name}")
    return match.group(1)


def normalized(s: str) -> str:
    return re.sub(r"\s+", "", s)


def connected_components(adj: dict[int, set[int]], removed: set[int]):
    remaining = set(adj) - removed
    components = []
    while remaining:
        component = set()
        pending = [remaining.pop()]
        while pending:
            v = pending.pop()
            component.add(v)
            newly_seen = remaining & adj[v]
            remaining.difference_update(newly_seen)
            pending.extend(newly_seen)
        components.append(component)
    return components


class TC063DuboisTwoComponentTest(unittest.TestCase):
    def test_source_groups_partition_without_duplication(self):
        self.assertEqual(set(A) | set(B), set(range(40)))
        self.assertFalse(set(A) & set(B))
        for label, group_ids in (("A", A), ("B", B)):
            definition = body(BRIDGE, f"component{label}CNF")
            self.assertEqual(
                [int(i) for i in re.findall(r"sourceGroup(\d+) bits = true", definition)],
                list(group_ids),
            )

    def test_actual_primal_graph_separator_and_component_ownership(self):
        adjacency = {v: set() for v in range(1, 61)}
        for equation in EQS:
            for a, b in itertools.combinations(equation["variables"], 2):
                adjacency[a].add(b)
                adjacency[b].add(a)
        self.assertEqual([len(c) for c in connected_components(adjacency, set())], [60])
        self.assertEqual(
            sorted(map(len, connected_components(adjacency, SEPARATOR))),
            [29, 29],
        )
        two_vertex_cuts = [
            pair for pair in itertools.combinations(range(1, 61), 2)
            if len(connected_components(adjacency, set(pair))) > 1
        ]
        self.assertEqual(len(two_vertex_cuts), 19)
        self.assertIn((10, 29), two_vertex_cuts)
        components = connected_components(adjacency, SEPARATOR)
        for group_ids in (A, B):
            variables = set().union(*(set(EQS[i]["variables"]) - SEPARATOR for i in group_ids))
            self.assertIn(variables, components)
            self.assertEqual(len(variables), 29)
        # A singleton is not a primal-graph separator here.
        for v in SEPARATOR:
            self.assertEqual(len(connected_components(adjacency, {v})), 1)

    def test_residual_groups_are_literal_separator_substitutions(self):
        for group_id, bit_index, assigned_name in (
            (9, 9, "s10"),
            (10, 9, "s10"),
            (29, 28, "s29"),
            (30, 28, "s29"),
        ):
            original = body(SOURCE, f"sourceGroup{group_id}")
            substituted = original.replace(f"(bits.getLsbD {bit_index})", assigned_name)
            self.assertNotEqual(substituted, original)
            self.assertEqual(
                normalized(substituted),
                normalized(body(BRIDGE, f"residualGroup{group_id}")),
            )
        for group_id in set(range(40)) - {9, 10, 29, 30}:
            original = body(SOURCE, f"sourceGroup{group_id}")
            self.assertNotIn("getLsbD 9)", original)
            self.assertNotIn("getLsbD 28)", original)
        for label, group_ids, substitutions in (
            ("A", A, {9: "residualGroup9 s10", 30: "residualGroup30 s29"}),
            ("B", B, {10: "residualGroup10 s10", 29: "residualGroup29 s29"}),
        ):
            definition = body(BRIDGE, f"component{label}Residual")
            actual = re.findall(r"(sourceGroup\d+|residualGroup\d+ s10|residualGroup\d+ s29) bits = true", definition)
            expected = [substitutions.get(i, f"sourceGroup{i}") for i in group_ids]
            self.assertEqual(actual, expected)

    def test_independent_component_xor_consequences_cover_all_four_branches(self):
        derived = []
        for group_ids in (A, B):
            occurrences = {}
            rhs = 0
            for i in group_ids:
                row = EQS[i]
                rhs ^= row["rhs"]
                for variable in row["variables"]:
                    occurrences[variable] = occurrences.get(variable, 0) ^ 1
            self.assertEqual({v for v, count in occurrences.items() if count}, SEPARATOR)
            derived.append(rhs)
        self.assertEqual(derived, [1, 0])
        for s10, s29 in itertools.product((0, 1), repeat=2):
            parity = s10 ^ s29
            self.assertTrue(parity != derived[0] or parity != derived[1])


if __name__ == "__main__":
    unittest.main()
