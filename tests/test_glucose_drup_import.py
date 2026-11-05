"""Independent Glucose DRUP import with fail-closed witness checks."""
from __future__ import annotations

from dataclasses import replace
import unittest

from scripts.generate_glucose_drup_rup_lean import glucose_drup_witness
from witnora_core.rup_witness_import import (
    annotate_drup, verify_native_witness,
)


class GlucoseDRUPImportTests(unittest.TestCase):
    def test_real_cdcl_proof_non_affine_pigeonholes(self) -> None:
        for pigeons, holes in [(3, 2), (4, 3)]:
            with self.subTest(size=(pigeons, holes)):
                raw, info = glucose_drup_witness(pigeons, holes)
                self.assertEqual(info["status"], "LEAN_CHECK_PENDING")
                self.assertGreater(len(info["additions"]), 0)
                self.assertEqual(info["additions"][-1].clause, ())
                self.assertTrue(verify_native_witness(raw, info["additions"]))

    def test_forged_unit_witness_rejected(self) -> None:
        raw, info = glucose_drup_witness(3, 2)
        trace = info["additions"]
        forged = trace[:-1] + [replace(trace[-1], units=(999,))]
        self.assertFalse(verify_native_witness(raw, forged))

    def test_missing_source_rows_rejected(self) -> None:
        raw, info = glucose_drup_witness(3, 2)
        trace = info["additions"]
        self.assertFalse(verify_native_witness([], trace))

    def test_wrong_proof_instant_rejection(self) -> None:
        with self.assertRaises(ValueError):
            annotate_drup([[1]], ["0"])

    def test_deletions_are_ignored_without_affecting_soundness(self) -> None:
        info = annotate_drup([[1], [-1]], ["d 1 0", "0"])
        self.assertEqual(info["deletions_ignored"], 1)
        self.assertEqual(info["status"], "LEAN_CHECK_PENDING")
        self.assertTrue(verify_native_witness([[1], [-1]], info["additions"]))


if __name__ == "__main__":
    unittest.main()
