"""Independent native negative controls for witness-carrying RUP traces."""
from __future__ import annotations

from dataclasses import replace
import unittest

from scripts.generate_general_rup_lean import (
    from_resolution, witness_accepts,
)
from witnora_core.ood_sat_families import pigeonhole


class GeneralRupTests(unittest.TestCase):
    def test_non_affine_pigeonhole_witness(self) -> None:
        raw = pigeonhole(3, 2).to_clause_lists()
        trace = from_resolution(raw)
        self.assertGreater(len(trace), 10)
        self.assertTrue(witness_accepts(raw, trace))
        self.assertEqual(trace[-1].clause, ())

    def test_missing_final_propagation_fails(self) -> None:
        raw = pigeonhole(3, 2).to_clause_lists()
        trace = from_resolution(raw)
        forged = trace[:-1] + [replace(trace[-1], units=())]
        self.assertFalse(witness_accepts(raw, forged))

    def test_wrong_forced_pivot_fails(self) -> None:
        raw = pigeonhole(3, 2).to_clause_lists()
        trace = from_resolution(raw)
        forged = [replace(trace[0], units=(999,))] + trace[1:]
        self.assertFalse(witness_accepts(raw, forged))

    def test_incomplete_proof_not_unsat(self) -> None:
        raw = pigeonhole(3, 2).to_clause_lists()
        self.assertFalse(witness_accepts(raw, from_resolution(raw)[:-1]))

    def test_nonoriginal_input_fails(self) -> None:
        raw = pigeonhole(3, 2).to_clause_lists()
        trace = from_resolution(raw)
        self.assertFalse(witness_accepts([], trace))


if __name__ == "__main__":
    unittest.main()
