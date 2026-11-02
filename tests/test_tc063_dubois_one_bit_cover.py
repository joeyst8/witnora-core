"""Fixture audit for the source-exact TC-063 Dubois20 Boolean cover bridge.

The Lean kernel checks the proof. This independent source audit ensures the
residual clause expressions are literal substitution of DIMACS variable 1.
"""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "theory" / "Dubois20SourceUnsat.lean").read_text()
BRIDGE = (ROOT / "theory" / "TC063DuboisOneBitCover.lean").read_text()


def definition(text: str, name: str) -> str:
    found = re.search(
        rf"(?ms)^def {name} \([^\n]*\) : (?:Bool|Prop) :=\n(.*?)(?=\n(?:def |theorem |end |#print |-- ))",
        text,
    )
    if found is None:
        raise AssertionError(f"Missing or malformed definition: {name}")
    return found.group(1)


def normalized(value: str) -> str:
    return re.sub(r"\s+", "", value)


class TC063DuboisOneBitCoverFixtureTest(unittest.TestCase):
    def test_affected_groups_are_literal_bit_zero_substitution(self):
        for i in (0, 1):
            original = definition(SOURCE, f"sourceGroup{i}")
            substituted = original.replace("(bits.getLsbD 0)", "branch")
            self.assertNotEqual(original, substituted)
            residual = definition(BRIDGE, f"residualGroup{i}")
            self.assertEqual(normalized(substituted), normalized(residual))

    def test_other_38_groups_are_unaffected_and_kept_once(self):
        tail = definition(BRIDGE, "residualCNF")
        self.assertEqual(
            re.findall(r"sourceGroup(\d+) bits = true", tail),
            [str(i) for i in range(2, 40)],
        )
        self.assertEqual(
            re.findall(r"residualGroup(\d+) branch bits = true", tail),
            ["0", "1"],
        )
        for i in range(2, 40):
            group = definition(SOURCE, f"sourceGroup{i}")
            self.assertNotIn("getLsbD 0", group)


if __name__ == "__main__":
    unittest.main()
