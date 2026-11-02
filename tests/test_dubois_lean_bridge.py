"""Fail-closed fixture and indexed-proof audit for PR #119's Lean Dubois theorem.

These Python assertions DO NOT replace the separate Lean kernel check.  They
protect the byte-for-byte correspondence between the archived row evidence and
the explicit formulas that Lean actually sees.
"""
from __future__ import annotations

import json
import unittest
from itertools import product
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHA = "82059aba0e5773644b386eb6bcbe53680655390cb041873a3cb3e93f7bd896a7"


def _lit(v: int) -> str:
    return f"(bits.getLsbD {v - 1})" if v > 0 else f"(!(bits.getLsbD {-v - 1}))"


def _section(text: str, head: str) -> str:
    match = text.find(head)
    if match == -1:
        raise AssertionError(f"Lean definition is missing: {head}")
    return text[match:].split("\n\n", 1)[0]


class DuboisLeanBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads((ROOT / "research/PR119_DUBOIS20_SOURCE_XOR_CERTIFICATE.json").read_text())
        cls.trace = json.loads((ROOT / "research/PR119_DUBOIS20_GF2_39_STEP_TRACE.json").read_text())
        cls.lean = (ROOT / "theory/Dubois20SourceUnsat.lean").read_text()

    def test_source_row_group_matches_four_original_clauses(self):
        source = self.source
        self.assertEqual(source["source_sha256"], SHA)
        self.assertEqual(source["original_variables"], 60)
        self.assertEqual(source["original_clauses"], 160)
        self.assertEqual(len(source["proof_equations"]), 40)
        seen = set()
        for i, row in enumerate(source["proof_equations"]):
            vs = row["variables"]
            self.assertEqual(len(vs), 3)
            self.assertEqual(len(set(vs)), 3)
            self.assertEqual(len(row["source_clauses"]), 4)
            for clause in row["source_clauses"]:
                self.assertEqual(len(clause), 3)
                self.assertEqual({abs(v) for v in clause}, set(vs))
                seen.add(tuple(sorted(clause)))
            for values in product((0, 1), repeat=3):
                assign = dict(zip(vs, values))
                cnf = all(any(assign[abs(l)] == (l > 0) for l in clause)
                          for clause in row["source_clauses"])
                parity = (sum(values) % 2) == row["rhs"]
                self.assertEqual(cnf, parity, f"source XOR row {i} failed")
            expected = (f"def sourceGroup{i} (bits : BitVec 60) : Bool :=\n  "
                        + " &&\n  ".join("(" + " || ".join(map(_lit, clause)) + ")"
                                            for clause in row["source_clauses"]))
            self.assertEqual(_section(self.lean, f"def sourceGroup{i} ("), expected)
            expected_parity = (f"def parity{i} (bits : BitVec 60) : Bool :=\n  ("
                               + " ^^ ".join(f"(bits.getLsbD {v - 1})" for v in vs) + ")")
            self.assertEqual(_section(self.lean, f"def parity{i} ("), expected_parity)
        self.assertEqual(len(seen), 160)

    def test_lean_source_and_certificate_conjunctions_are_complete(self):
        rows = self.source["proof_equations"]
        expected_cnf = ("def sourceCNF (bits : BitVec 60) : Prop :=\n    "
                        + " ∧\n    ".join(f"sourceGroup{i} bits = true" for i in range(40)))
        expected_rows = ("def certificateRows (bits : BitVec 60) : Prop :=\n    "
                         + " ∧\n    ".join(f"parity{i} bits = " + ("true" if r["rhs"] else "false")
                                               for i, r in enumerate(rows)))
        self.assertEqual(_section(self.lean, "def sourceCNF ("), expected_cnf)
        self.assertEqual(_section(self.lean, "def certificateRows ("), expected_rows)
        self.assertIn("theorem source_unsat (bits : BitVec 60) : ¬ sourceCNF bits", self.lean)
        self.assertNotIn("bv_decide", self.lean)
        self.assertNotIn("native_decide", self.lean)
        self.assertNotIn("sorry", self.lean)

    def test_indexed_trace_matches_lean_and_ends_in_contradiction(self):
        data = self.trace
        self.assertEqual(data["decompressed_sha256"], SHA)
        self.assertEqual(data["xor_operations"], 39)
        self.assertEqual(len(data["steps"]), 39)
        all_rows = {i: (tuple(e["variables"]), e["rhs"])
                    for i, e in enumerate(self.source["proof_equations"])}
        for index, step in enumerate(data["steps"]):
            rid = index + 40
            self.assertEqual(step["id"], rid)
            left_id, right_id = step["left_id"], step["right_id"]
            self.assertLess(left_id, rid)
            self.assertLess(right_id, rid)
            left_vars, left_rhs = all_rows[left_id]
            right_vars, right_rhs = all_rows[right_id]
            expected_vars = tuple(sorted(set(left_vars) ^ set(right_vars)))
            self.assertEqual(tuple(step["variables"]), expected_vars)
            self.assertEqual(step["rhs"], left_rhs ^ right_rhs)
            self.assertLessEqual(len(expected_vars), 4)
            self.assertLessEqual(len(set(left_vars) | set(right_vars)), 5)
            expected_def = (f"def traceRow{rid} (bits : BitVec 60) : Bool := "
                            + ("(" + " ^^ ".join(f"(bits.getLsbD {v - 1})"
                                                for v in expected_vars) + ")" if expected_vars else "false"))
            self.assertEqual(_section(self.lean, f"def traceRow{rid} ("), expected_def)
            left_name = f"parity{left_id}" if left_id < 40 else f"traceRow{left_id}"
            right_name = f"parity{right_id}" if right_id < 40 else f"traceRow{right_id}"
            self.assertIn(f"have hxor : traceRow{rid} bits = ({left_name} bits ^^ {right_name} bits)", self.lean)
            all_rows[rid] = (expected_vars, step["rhs"])
        self.assertEqual(all_rows[78], ((), 1))
        self.assertEqual(data["final_row_id"], 78)
        self.assertEqual(data["final_row_rhs"], 1)


if __name__ == "__main__":
    unittest.main()
