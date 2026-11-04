"""R-032 native incidence component certificate evidence parity and attacks."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import random
import unittest

from witnora_core.certificate import StepLogger
from witnora_core.cnf import CNFFormula
from witnora_core.components import component_details
from witnora_core.dimacs import parse_dimacs
from witnora_core.verifier import _verify_cd_step


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestNativeComponentEvidence(unittest.TestCase):
    def test_1400_randomized_all_component_fields_and_python_replay(self):
        rng = random.Random(320112026)
        cases = 0
        for n in range(1, 8):
            for _ in range(200):
                clauses = [
                    [rng.choice((-1,1))*rng.randrange(1,n+1)
                     for _ in range(rng.randrange(5))]
                    for _ in range(rng.randrange(13))
                ]
                formula = CNFFormula.from_raw_clauses(clauses)
                expected = component_details(formula)
                native = component_details(formula, backend="rust_details")
                with self.subTest(n=n, source=clauses):
                    self.assertEqual(native, expected)
                    logger = StepLogger()
                    step = logger.append(
                        "CD", formula, formula, details=native)
                    ok, children, error = _verify_cd_step(step, formula)
                    self.assertTrue(ok, error)
                    self.assertEqual(len(children), native["component_count"])
                cases += 1
        self.assertEqual(cases, 1400)

    def test_real_multicomponent_and_forged_index_rejection(self):
        examples = Path(__file__).resolve().parents[1] / "examples"
        formula = parse_dimacs(
            (examples / "multi_component_demo.dimacs").read_text(encoding="utf-8"))
        native = component_details(formula, backend="rust_details")
        self.assertEqual(native, component_details(formula))
        self.assertGreater(len(native["components"]), 1)
        step = StepLogger().append("CD", formula, formula, details=native)
        self.assertTrue(_verify_cd_step(step, formula)[0])
        forged = deepcopy(native)
        forged["components"][0]["clause_indices"] = [999]
        bad = StepLogger().append("CD", formula, formula, details=forged)
        ok, _, error = _verify_cd_step(bad, formula)
        self.assertFalse(ok)
        self.assertEqual(error, "CD component contents mismatch")


if __name__ == "__main__":
    unittest.main()
