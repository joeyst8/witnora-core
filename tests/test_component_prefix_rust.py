"""R-036: local root prefix + one native CD + component-local suffix."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import os
import random
import unittest

from witnora_core.certificate import CollapsePath, StepLogger
from witnora_core.cnf import CNFFormula
from witnora_core.components import component_details
from witnora_core.simplify import _unit_step
from witnora_core.verifier import verify_collapse_path
from witnora_core.verifier_rust import replay_prefixed_component_certificate_in_rust


def make_path(rng):
    source = [[1], [-1, 2], [-1, 3], [4, 5]]
    rng.shuffle(source)
    original = CNFFormula.from_raw_clauses(source)
    log = StepLogger()
    intermediate, proof = _unit_step(original)
    assert intermediate is not None
    removed = proof["satisfied_clauses"] + [
        item["from"] for item in proof["shortened_clauses"]
    ]
    added = [item["to"] for item in proof["shortened_clauses"]]
    log.append("UP", original, intermediate, details=proof,
               removed_clauses=removed, added_clauses=added,
               assigned_literals=[proof["assigned_literal"]])
    cd_details = component_details(intermediate)
    assert cd_details["component_count"] >= 2
    log.append("CD", intermediate, intermediate, details=cd_details)
    states = {
        str(row["component_id"]):
            CNFFormula.from_raw_clauses(row["clauses"])
        for row in cd_details["components"]
    }
    for component_id in sorted(states):
        outcome = _unit_step(states[component_id])
        if outcome is None:
            continue
        next_state, proof = outcome
        removed = proof["satisfied_clauses"] + [
            item["from"] for item in proof["shortened_clauses"]
        ]
        added = [item["to"] for item in proof["shortened_clauses"]]
        log.append("UP", states[component_id], next_state,
                   details=dict(proof, component_id=component_id),
                   removed_clauses=removed, added_clauses=added,
                   assigned_literals=[proof["assigned_literal"]])
        states[component_id] = next_state
    final = CNFFormula(clause for cid in sorted(states)
                       for clause in states[cid].clauses)
    path = CollapsePath(
        original_formula_hash=original.formula_hash,
        c_parameter=4, steps=log.steps,
        final_formula_hash=final.formula_hash,
        final_class="COMPONENT_LOCAL_REPLAY",
        status="NO_COLLAPSE_FOUND_UNDER_CURRENT_GRAMMAR_AND_C",
    )
    return original, path, final


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestPrefixedComponentReplay(unittest.TestCase):
    def assert_same(self, original, path, expected, good):
        reference = verify_collapse_path(original, path)
        native_ok, native_final, native_err = (
            replay_prefixed_component_certificate_in_rust(
                original, path.steps, path.c_parameter, path.final_formula_hash))
        self.assertEqual(native_ok, good)
        self.assertEqual(reference.ok, good, reference.errors)
        self.assertEqual(native_err, reference.errors[0] if reference.errors else None)
        if good:
            self.assertEqual(native_final, expected)

    def test_240_prefixed_component_streams_with_attacks(self):
        rng = random.Random(361112026)
        for case in range(240):
            original, path, final = make_path(rng)
            with self.subTest(case=case):
                self.assert_same(original, path, final, True)
                before = replace(path.steps[0], assigned_literals=[999])
                self.assert_same(original, replace(path, steps=[
                    before, *path.steps[1:]]), final, False)
                wrong_cd = replace(path.steps[1],
                    input_formula_hash="0"*64)
                self.assert_same(original, replace(path, steps=[
                    path.steps[0], wrong_cd, *path.steps[2:]]), final, False)
                altered = deepcopy(path.steps[1].details)
                altered["component_count"] += 1
                wrong_count = replace(path.steps[1], details=altered)
                self.assert_same(original, replace(path, steps=[
                    path.steps[0], wrong_count, *path.steps[2:]]), final, False)
                self.assert_same(original,
                    replace(path, final_formula_hash="0"*64), final, False)
                self.assertGreater(len(path.steps), 2)
                wrong_scope = replace(path.steps[2],
                    details=dict(path.steps[2].details,
                                 component_id="not_a_component"))
                self.assert_same(original, replace(path, steps=[
                    *path.steps[:2], wrong_scope, *path.steps[3:]]),
                    final, False)


if __name__ == "__main__":
    unittest.main()
