"""R-024 exact Rust StepLogger record parity against Python certificate records."""
from __future__ import annotations

import os
import random
import unittest

from witnora_core.certificate import StepLogger
from witnora_core.cnf import CNFFormula


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestRustStepRecords(unittest.TestCase):
    def test_1200_randomized_full_certificate_step_records(self):
        rng = random.Random(240112026)
        py = StepLogger()
        rust = StepLogger(backend="rust")
        for n in range(1, 9):
            for case in range(150):
                make = lambda: [
                    [rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                     for _ in range(rng.randrange(5))]
                    for _ in range(rng.randrange(10))
                ]
                before = CNFFormula.from_raw_clauses(make())
                after = CNFFormula.from_raw_clauses(make())
                details = {"status": rng.choice(["SAT", "UNSAT", "OPEN"]),
                           "nested": {"case": case, "values": [case, n]}}
                removed = before.to_clause_lists()[:3]
                added = after.to_clause_lists()[:2]
                assigned = [rng.choice((-1, 1)) * rng.randrange(1, n + 1)]
                reconstruction = {"variable": n, "positive": case % 2 == 0}
                kwargs = dict(
                    details=details, removed_clauses=removed,
                    added_clauses=added, assigned_literals=assigned,
                    reconstruction_data=reconstruction,
                )
                left = py.append("VE", before, after, **kwargs).to_dict()
                right = rust.append("VE", before, after, **kwargs).to_dict()
                with self.subTest(n=n, case=case):
                    self.assertEqual(right, left)
                    self.assertEqual(list(right), list(left))
                    self.assertEqual(right["step_id"], len(py.steps))
        self.assertEqual(len(py.steps), 1200)

    def test_empty_defaults_and_reused_formula(self):
        before = CNFFormula.from_raw_clauses([])
        for args in ((before, before),):
            left = StepLogger().append("BCE", *args).to_dict()
            right = StepLogger(backend="rust").append("BCE", *args).to_dict()
            self.assertEqual(right, left)

    def test_unknown_backend_and_invalid_step_id(self):
        with self.assertRaisesRegex(ValueError, "unknown"):
            StepLogger(backend="not-an-engine")
        from witnora_ve import build_step_record_native
        with self.assertRaises(ValueError):
            build_step_record_native(0, "UP", [], [], {}, [], [], [], {})
        with self.assertRaises(ValueError):
            build_step_record_native(1, "UP", [[0]], [], {}, [], [], [], {})


if __name__ == "__main__":
    unittest.main()
