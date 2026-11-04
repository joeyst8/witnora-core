"""R-030 strict Rust local certificate replay differential and tamper cases."""
from __future__ import annotations

from dataclasses import replace
import os
import random
import unittest

from witnora_core.bce import find_first_blocked_clause
from witnora_core.certificate import StepLogger
from witnora_core.cnf import CNFFormula
from witnora_core.simplify import _pure_literal_step, _unit_step, simplify
from witnora_core.subsumption import find_first_subsumption
from witnora_core.ve import eliminate_variable
from witnora_core.verifier import (
    _verify_up, _verify_ple, _verify_sub, _verify_bce, _verify_ve,
)
from witnora_core.verifier_rust import replay_local_certificate_in_rust


def sample_step(kind, source):
    formula = CNFFormula.from_raw_clauses(source)
    logger = StepLogger()
    if kind == "UP":
        out = _unit_step(formula)
        if out is None:
            return None
        output, details = out
        removed = details["satisfied_clauses"] + [
            row["from"] for row in details["shortened_clauses"]
        ]
        added = [row["to"] for row in details["shortened_clauses"]]
        logger.append("UP", formula, output, details=details,
                      removed_clauses=removed, added_clauses=added,
                      assigned_literals=[details["assigned_literal"]])
    elif kind == "PLE":
        out = _pure_literal_step(formula)
        if out is None:
            return None
        output, details = out
        logger.append("PLE", formula, output, details=details,
                      removed_clauses=details["removed_due_to_pure_literal"],
                      assigned_literals=[details["assigned_literal"]])
    elif kind == "SUB":
        pair = find_first_subsumption(formula)
        if pair is None:
            return None
        subsumer, removed = pair
        output = formula.without_clause(removed)
        logger.append("SUB", formula, output,
                      details={"subsuming_clause": subsumer.to_list()},
                      removed_clauses=[removed.to_list()])
    elif kind == "BCE":
        pair = find_first_blocked_clause(formula)
        if pair is None:
            return None
        removed, proof = pair
        output = formula.without_clause(removed)
        logger.append("BCE", formula, output, details=proof,
                      removed_clauses=[removed.to_list()])
    elif kind == "VE":
        status, output, _ = eliminate_variable(formula, 1, 4, logger=logger)
        if status != "OK":
            return None
    else:
        raise ValueError(kind)
    return formula, output, logger.steps[0]


def original_local_step(kind, step, formula):
    if kind == "UP":
        return _verify_up(step, formula)
    if kind == "PLE":
        return _verify_ple(step, formula)
    if kind == "SUB":
        return _verify_sub(step, formula)
    if kind == "BCE":
        return _verify_bce(step, formula)
    return _verify_ve(step, formula, 4)


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestNativeLocalReplay(unittest.TestCase):
    def test_1000_valid_local_steps_and_1000_tampered_outputs(self):
        rng = random.Random(300112026)
        sources = {
            "UP": [[1], [-1, 2], [3, 4]],
            "PLE": [[1, 2], [-2, 3]],
            "SUB": [[1], [1, 2], [-2, 3]],
            "BCE": [[1, 2], [-1, -2], [3, 4]],
            "VE": [[1, 2], [-1, 3], [2, -3]],
        }
        tested = 0
        for kind, original in sources.items():
            for case in range(200):
                # Preserve the VE pivot 1 while randomizing other names and signs.
                mapping = {1: 1, 2: rng.randrange(2, 10),
                           3: rng.randrange(10, 18), 4: rng.randrange(18, 26)}
                flipped = {var: (-1 if rng.getrandbits(1) else 1)
                           for var in mapping}
                if kind == "VE":
                    flipped[1] = 1
                source = [
                    [(-1 if lit < 0 else 1) * flipped[abs(lit)] * mapping[abs(lit)]
                     for lit in clause]
                    for clause in original
                ]
                rng.shuffle(source)
                got = sample_step(kind, source)
                self.assertIsNotNone(got, kind)
                formula, output, step = got
                good, actual, error = replay_local_certificate_in_rust(
                    formula, [step], 4, output.formula_hash)
                with self.subTest(kind=kind, case=case):
                    self.assertTrue(good, error)
                    self.assertIsNone(error)
                    self.assertEqual(actual, output)
                    py_ok, py_next, py_error = original_local_step(
                        kind, step, formula)
                    self.assertTrue(py_ok, py_error)
                    self.assertEqual(py_next, actual)

                bad = replace(step, output_formula_hash="0" * 64)
                bad_ok, _, bad_error = replay_local_certificate_in_rust(
                    formula, [bad], 4, output.formula_hash)
                ref_ok, _, ref_error = original_local_step(kind, bad, formula)
                with self.subTest(kind=kind, case=case, tampered=True):
                    self.assertFalse(bad_ok)
                    self.assertFalse(ref_ok)
                    self.assertEqual(bad_error, f"step 1: {ref_error}")
                tested += 1
        self.assertEqual(tested, 1000)

    def test_complete_simplification_sequences(self):
        sources = (
            [[1], [-1, 2], [3, 4]],
            [[1, 2], [-2, 3], [4, 5]],
            [[1, 2], [-1, -2], [3, 4]],
        )
        for source in sources:
            original = CNFFormula.from_raw_clauses(source)
            logger = StepLogger()
            out, _ = simplify(original, logger, log_component_decomposition=False)
            with self.subTest(source=source):
                good, replayed, error = replay_local_certificate_in_rust(
                    original, logger.steps, 5, out.formula_hash)
                self.assertTrue(good, error)
                self.assertEqual(out, replayed)

    def test_component_or_unknown_rejected(self):
        from witnora_core.certificate import CollapseStep
        formula = CNFFormula.from_raw_clauses([[1]])
        step = CollapseStep(
            step_id=1, type="CD",
            input_formula_hash=formula.formula_hash,
            output_formula_hash=formula.formula_hash)
        with self.assertRaisesRegex(ValueError, "unsupported"):
            replay_local_certificate_in_rust(
                formula, [step], 2, formula.formula_hash)


if __name__ == "__main__":
    unittest.main()
