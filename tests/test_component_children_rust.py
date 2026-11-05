"""R-034: Rust CD evidence checker returns only valid canonical child states."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import os
from pathlib import Path
import random
import unittest

from witnora_core.certificate import StepLogger
from witnora_core.cnf import CNFFormula
from witnora_core.components import component_details
from witnora_core.dimacs import parse_dimacs
from witnora_core.verifier import _verify_cd_step
from witnora_core.verifier_rust import verify_cd_step_in_rust


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestNativeComponentChildStates(unittest.TestCase):
    def assert_cd_same(self, step, formula):
        py_ok, py_children, py_error = _verify_cd_step(step, formula)
        rs_ok, rs_children, rs_error = verify_cd_step_in_rust(step, formula)
        self.assertEqual((rs_ok, rs_error), (py_ok, py_error))
        self.assertEqual(
            {k: v.to_clause_lists() for k, v in rs_children.items()},
            {k: v.to_clause_lists() for k, v in py_children.items()},
        )
        if not rs_ok:
            self.assertEqual(rs_children, {})

    def test_1440_random_native_component_children_and_tamper_rejection(self):
        rng = random.Random(341112026)
        cases = 0
        for n in range(1, 9):
            for _ in range(180):
                source = [
                    [rng.choice((-1, 1))*rng.randrange(1, n+1)
                     for _ in range(rng.randrange(5))]
                    for _ in range(rng.randrange(13))
                ]
                formula = CNFFormula.from_raw_clauses(source)
                evidence = component_details(formula, backend="rust_details")
                step = StepLogger().append("CD", formula, formula, details=evidence)
                with self.subTest(n=n, source=source):
                    self.assert_cd_same(step, formula)
                    bad = deepcopy(evidence)
                    bad["component_count"] += 1
                    self.assert_cd_same(replace(step, details=bad), formula)
                    bad = deepcopy(evidence)
                    bad["incidence_edges"].append([999, 0])
                    self.assert_cd_same(replace(step, details=bad), formula)
                    if evidence["components"]:
                        bad = deepcopy(evidence)
                        bad["components"][0]["clause_indices"] = [999]
                        self.assert_cd_same(replace(step, details=bad), formula)
                    self.assert_cd_same(
                        replace(step, output_formula_hash="0"*64), formula)
                cases += 1
        self.assertEqual(cases, 1440)

    def test_multicomponent_fixture_has_identical_authenticated_children(self):
        fixture = (Path(__file__).resolve().parents[1] / "examples" /
                   "multi_component_demo.dimacs")
        formula = parse_dimacs(fixture.read_text(encoding="utf-8"))
        step = StepLogger().append(
            "CD", formula, formula,
            details=component_details(formula, backend="rust_details"))
        self.assertGreater(step.details["component_count"], 1)
        self.assert_cd_same(step, formula)


if __name__ == "__main__":
    unittest.main()
