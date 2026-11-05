"""Opt-in indexed propagation must produce independently replayable RUP witnesses."""
from __future__ import annotations

from random import Random
import unittest

from pysat.solvers import Glucose3

from witnora_core.ood_sat_families import pigeonhole
from witnora_core.rup_indexed_propagation import indexed_unit_conflict_witness
from witnora_core.rup_witness_import import (
    annotate_drup, unit_conflict_witness, verify_native_witness,
)


def valid_single(database: list[tuple[int, ...]], target: tuple[int, ...],
                 units: tuple[int, ...]) -> bool:
    assumptions = {-lit for lit in target}
    for lit in units:
        if not any(lit in row and all(x == lit or -x in assumptions for x in row)
                   for row in database):
            return False
        assumptions.add(lit)
    return any(all(-lit in assumptions for lit in row) for row in database)


class IndexedPropagationTests(unittest.TestCase):
    def test_small_random_replay_and_reference_result(self) -> None:
        rng = Random(630063)
        for _ in range(300):
            db = []
            for _ in range(rng.randrange(1, 9)):
                vs = rng.sample([1, 2, 3, 4, 5], rng.randrange(1, 4))
                db.append(tuple(sorted((v if rng.randrange(2) else -v for v in vs))))
            vs = rng.sample([1, 2, 3, 4, 5], rng.randrange(0, 4))
            target = tuple(v if rng.randrange(2) else -v for v in vs)
            reference = unit_conflict_witness(db, target)
            indexed = indexed_unit_conflict_witness(db, target)
            self.assertEqual(reference is None, indexed is None,
                             msg=f"DB={db!r}, target={target!r}")
            if indexed is not None:
                self.assertTrue(valid_single(db, target, indexed))

    def test_glucose_proof_php_five_four_and_six_five(self) -> None:
        for n, m in [(5, 4), (6, 5)]:
            with self.subTest(size=(n, m)):
                raw = pigeonhole(n, m).to_clause_lists()
                with Glucose3(bootstrap_with=raw, with_proof=True) as solver:
                    self.assertFalse(solver.solve())
                    proof = solver.get_proof()
                fast = annotate_drup(raw, proof, indexed_propagation=True)
                self.assertEqual(fast["status"], "LEAN_CHECK_PENDING")
                self.assertEqual(fast["witness_algorithm"], "indexed_occurrence")
                self.assertTrue(verify_native_witness(raw, fast["additions"]))
                slow = annotate_drup(raw, proof, indexed_propagation=False)
                self.assertTrue(verify_native_witness(raw, slow["additions"]))
                self.assertEqual([x.clause for x in fast["additions"]],
                                 [x.clause for x in slow["additions"]])


if __name__ == "__main__":
    unittest.main()
