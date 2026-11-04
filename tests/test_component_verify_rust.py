"""R-033 independent Rust CD checker: success and exact tamper reason parity."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import os
import random
import unittest

from witnora_core.certificate import StepLogger
from witnora_core.cnf import CNFFormula
from witnora_core.components import (
    component_details, verify_component_evidence_in_rust,
)
from witnora_core.verifier import _verify_cd_step


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestNativeComponentVerifier(unittest.TestCase):
    def _assert_matches_python(self, formula, evidence, output_hash):
        base = StepLogger().append("CD", formula, formula, details=evidence)
        step = replace(base, output_formula_hash=output_hash)
        accepted, _, python_error = _verify_cd_step(step, formula)
        native_error = verify_component_evidence_in_rust(
            formula, evidence, output_hash)
        self.assertEqual(native_error, python_error)
        self.assertEqual(native_error is None, accepted)

    def test_1200_seeded_valid_and_corrupted_component_proofs(self):
        rng = random.Random(331112026)
        cases = 0
        mutations = 0
        for n in range(1, 7):
            for _ in range(200):
                clauses = [
                    [rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                     for _ in range(rng.randrange(5))]
                    for _ in range(rng.randrange(13))
                ]
                formula = CNFFormula.from_raw_clauses(clauses)
                expected = component_details(formula)
                with self.subTest(n=n, source=clauses):
                    self._assert_matches_python(
                        formula, expected, formula.formula_hash)
                    corrupted = deepcopy(expected)
                    corrupted["component_count"] += 1
                    self._assert_matches_python(
                        formula, corrupted, formula.formula_hash)
                    corrupted = deepcopy(expected)
                    corrupted["incidence_edges"].append([9999, 0])
                    self._assert_matches_python(
                        formula, corrupted, formula.formula_hash)
                    if expected["components"]:
                        corrupted = deepcopy(expected)
                        corrupted["components"][0]["formula_hash"] = "0" * 64
                        self._assert_matches_python(
                            formula, corrupted, formula.formula_hash)
                        corrupted = deepcopy(expected)
                        corrupted["components"][0]["clause_indices"] = [9999]
                        self._assert_matches_python(
                            formula, corrupted, formula.formula_hash)
                        mutations += 2
                    self._assert_matches_python(formula, expected, "0" * 64)
                    mutations += 3
                cases += 1
        self.assertEqual(cases, 1200)
        self.assertGreater(mutations, 4000)


if __name__ == "__main__":
    unittest.main()
