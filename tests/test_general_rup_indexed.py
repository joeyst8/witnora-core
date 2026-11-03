"""Real Glucose DRUP with explicit checked unit/conflict row IDs."""
from __future__ import annotations

from dataclasses import replace
import unittest

from scripts.generate_glucose_drup_rup_lean import glucose_drup_witness
from witnora_core.rup_witness_import import (
    attach_reason_indices,
    verify_native_indexed_witness,
)


class IndexedRUPRowTests(unittest.TestCase):
    def test_real_cdcl_certificate_and_reason_indices(self) -> None:
        for n, m in [(3, 2), (4, 3), (5, 4)]:
            with self.subTest(n=n, m=m):
                source, report = glucose_drup_witness(n, m, indexed=True)
                indexed = attach_reason_indices(source, report["additions"])
                self.assertTrue(verify_native_indexed_witness(source, indexed))
                self.assertEqual(indexed[-1].clause, ())
                self.assertEqual(len(indexed), len(report["additions"]))
                for i, step in enumerate(indexed):
                    database_size = len(source) + i
                    self.assertLess(step.conflict_id, database_size)
                    self.assertTrue(all(0 <= row_id < database_size
                                        for _, row_id in step.units))

    def test_tampered_reason_conflict_future_id_rejected(self) -> None:
        source, report = glucose_drup_witness(3, 2, indexed=True)
        proof = attach_reason_indices(source, report["additions"])
        self.assertTrue(proof[0].units)
        forged_units = ((proof[0].units[0][0], 999),) + proof[0].units[1:]
        wrong_unit = [replace(proof[0], units=forged_units)] + proof[1:]
        self.assertFalse(verify_native_indexed_witness(source, wrong_unit))
        wrong_conflict = [replace(proof[0], conflict_id=999)] + proof[1:]
        self.assertFalse(verify_native_indexed_witness(source, wrong_conflict))
        future_id = [replace(proof[0], conflict_id=len(source) + len(proof))] + proof[1:]
        self.assertFalse(verify_native_indexed_witness(source, future_id))

    def test_missing_source_rejected(self) -> None:
        source, report = glucose_drup_witness(3, 2, indexed=True)
        proof = attach_reason_indices(source, report["additions"])
        self.assertFalse(verify_native_indexed_witness([], proof))
        with self.assertRaises(ValueError):
            attach_reason_indices([], report["additions"])


if __name__ == "__main__":
    unittest.main()
