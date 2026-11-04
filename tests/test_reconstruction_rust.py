"""R-029 full SAT reconstruction Rust/Python differential tests."""
from __future__ import annotations

import json
import os
from pathlib import Path
import random
import tempfile
import unittest

from witnora_core.certificate import CollapseStep
from witnora_core.cnf import CNFFormula
from witnora_core.dimacs import parse_dimacs
from witnora_core.proof import collapse_path_from_result_dict, load_certificate_package
from witnora_core.reconstruction import reconstruct_assignment


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestRustReconstruction(unittest.TestCase):
    def test_1600_seeded_exact_assignment_and_failure_parity(self):
        rng = random.Random(290112026)
        operations = ("UP", "PLE", "BCE", "VE", "SUB",
                      "CD", "2SAT_SOLVE", "TREEWIDTH_SOLVE", "UNKNOWN")
        case = 0
        for n in range(1, 9):
            for _ in range(200):
                case += 1
                source = [
                    [rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                     for _ in range(rng.randrange(5))]
                    for _ in range(rng.randrange(10))
                ]
                formula = CNFFormula.from_raw_clauses(source)
                final = {
                    var: bool(rng.getrandbits(1))
                    for var in range(1, n + 1) if rng.getrandbits(1)
                }
                steps = []
                for i in range(rng.randrange(6)):
                    kind = rng.choice(operations)
                    assigned = [] if rng.randrange(5) == 0 else [
                        rng.choice((-1, 1)) * rng.randrange(1, n + 1)]
                    clause = [rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                              for _ in range(rng.randrange(4))]
                    others = [
                        [rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                         for _ in range(rng.randrange(4))]
                        for _ in range(rng.randrange(3))]
                    # Only use non-tautological clauses when Python Clause is used.
                    clause = list(CNFFormula.from_raw_clauses([clause]).to_clause_lists()[0]) \
                        if CNFFormula.from_raw_clauses([clause]).clauses else []
                    clean_others = []
                    for other in others:
                        normalized = CNFFormula.from_raw_clauses([other]).to_clause_lists()
                        if normalized:
                            clean_others.extend(normalized)
                    details = {
                        "removed_clause": clause,
                        "blocked_literal": rng.choice((-1, 1)) * rng.randrange(1, n + 1),
                        "opposite_clauses": clean_others,
                        "eliminated_variable": rng.randrange(1, n + 1),
                        "removed_clauses": clean_others,
                    }
                    steps.append(CollapseStep(
                        step_id=i + 1, type=kind, input_formula_hash="",
                        output_formula_hash="", assigned_literals=assigned,
                        reconstruction_data=details,
                    ))
                python = reconstruct_assignment(formula, steps, final)
                native = reconstruct_assignment(formula, steps, final, backend="rust")
                with self.subTest(case=case, n=n):
                    self.assertEqual(native.ok, python.ok)
                    self.assertEqual(native.error, python.error)
                    self.assertEqual(native.assignment, python.assignment)

    def test_real_sat_unsat_and_component_certificate_paths(self):
        from tests.test_certificate_export import run_export
        examples = Path(__file__).resolve().parents[1] / "examples"
        for name in ("bce_demo.dimacs", "unsat_demo.dimacs",
                     "multi_component_demo.dimacs"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                file = Path(tmp) / "reference.wcert"
                status, _ = run_export(name, 2, file)
                self.assertEqual(status, 0)
                _, files = load_certificate_package(file)
                path = collapse_path_from_result_dict(json.loads(files["result.json"]))
                formula = parse_dimacs((examples / name).read_text(encoding="utf-8"))
                reference = reconstruct_assignment(
                    formula, path.steps, path.final_assignment)
                native = reconstruct_assignment(
                    formula, path.steps, path.final_assignment, backend="rust")
                self.assertEqual(native, reference)

    def test_invalid_backend(self):
        with self.assertRaisesRegex(ValueError, "unknown"):
            reconstruct_assignment(
                CNFFormula.from_raw_clauses([]), [], {}, backend="unknown")


if __name__ == "__main__":
    unittest.main()
