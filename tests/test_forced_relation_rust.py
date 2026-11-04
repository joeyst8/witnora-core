"""R-039 bounded failed-literal Rust probing complete Python parity."""
from __future__ import annotations

import os
import random
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.forced_relation_probe import (
    unit_conflict, unit_conflict_rust,
    probe_forced_relations, probe_forced_relations_rust,
)


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestFailedLiteralNative(unittest.TestCase):
    def test_1000_random_conflicts_and_bounded_probe_outcomes(self):
        rng=random.Random(391112026)
        count=0
        for n in range(1,9):
            for case in range(125):
                source=[
                    [rng.choice((-1,1))*rng.randrange(1,n+1)
                     for _ in range(rng.randrange(5))]
                    for _ in range(rng.randrange(13))
                ]
                formula=CNFFormula.from_raw_clauses(source)
                assumption=(rng.choice((-1,1))*rng.randrange(1,n+1))
                budget=rng.randrange(0,min(n+2,12))
                with self.subTest(n=n,case=case,source=source):
                    self.assertEqual(unit_conflict_rust(formula,assumption),
                                     unit_conflict(formula,assumption))
                    py_form,py_meta=probe_forced_relations(
                        formula,max_probes=budget)
                    rs_form,rs_meta=probe_forced_relations_rust(
                        formula,max_probes=budget)
                    self.assertEqual(rs_form,py_form)
                    self.assertEqual(rs_meta,py_meta)
                count+=1
        self.assertEqual(count,1000)

    def test_ambivalent_conflict_and_invalid_budgets(self):
        formula=CNFFormula.from_raw_clauses([[1],[-1]])
        native,details=probe_forced_relations_rust(formula,max_probes=1)
        ref,meta=probe_forced_relations(formula,max_probes=1)
        self.assertEqual(native,ref)
        self.assertEqual(details,meta)
        self.assertTrue(details["both_assumptions_conflict"])
        for budget in (-1,257):
            with self.assertRaisesRegex(ValueError,
                                        "invalid bounded probing budget"):
                probe_forced_relations_rust(formula,max_probes=budget)
            with self.assertRaisesRegex(ValueError,
                                        "invalid bounded probing budget"):
                probe_forced_relations(formula,max_probes=budget)


if __name__=="__main__":
    unittest.main()
