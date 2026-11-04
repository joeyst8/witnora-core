"""R-035 native single-root component-context stream replay differential."""
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
from witnora_core.verifier_rust import replay_root_component_certificate_in_rust


def make_component_path(rng):
    # Independently variable-disjoint subgraphs, randomized but with units.
    source = [[1], [-1, 2], [4], [-4, 5]]
    for group in ((1, 2), (4, 5)):
        for _ in range(rng.randrange(4)):
            source.append([
                rng.choice((-1, 1)) * rng.choice(group)
                for _ in range(rng.randrange(1, 4))
            ])
    rng.shuffle(source)
    original = CNFFormula.from_raw_clauses(source)
    logger = StepLogger()
    details = component_details(original)
    assert details["component_count"] >= 2
    logger.append("CD", original, original, details=details)
    states = {
        str(item["component_id"]): CNFFormula.from_raw_clauses(item["clauses"])
        for item in details["components"]
    }
    for component_id in sorted(states):
        state = states[component_id]
        outcome = _unit_step(state)
        if outcome is None:
            continue
        next_state, evidence = outcome
        detail = dict(evidence, component_id=component_id)
        removed = evidence["satisfied_clauses"] + [
            entry["from"] for entry in evidence["shortened_clauses"]
        ]
        added = [entry["to"] for entry in evidence["shortened_clauses"]]
        logger.append("UP", state, next_state, details=detail,
                      removed_clauses=removed, added_clauses=added,
                      assigned_literals=[evidence["assigned_literal"]])
        states[component_id] = next_state
    final = CNFFormula(clause for cid in sorted(states)
                       for clause in states[cid].clauses)
    path = CollapsePath(
        original_formula_hash=original.formula_hash,
        c_parameter=4, steps=logger.steps,
        final_formula_hash=final.formula_hash,
        final_class="COMPONENT_LOCAL_REPLAY",
        status="NO_COLLAPSE_FOUND_UNDER_CURRENT_GRAMMAR_AND_C",
    )
    return original, path, final


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestNativeRootComponentStream(unittest.TestCase):
    def assert_matches(self, original, path, final, good):
        py = verify_collapse_path(original, path)
        rs_ok, rs_final, rs_error = replay_root_component_certificate_in_rust(
            original, path.steps, path.c_parameter, path.final_formula_hash)
        self.assertEqual(rs_ok, good)
        self.assertEqual(py.ok, good, py.errors)
        self.assertEqual(rs_error, py.errors[0] if py.errors else None)
        if good:
            self.assertEqual(rs_final, final)

    def test_360_seeded_paths_and_adversarial_context_mutations(self):
        rng = random.Random(351112026)
        for case in range(360):
            original, path, final = make_component_path(rng)
            with self.subTest(case=case):
                self.assert_matches(original, path, final, True)
                bad_details = deepcopy(path.steps[0].details)
                bad_details["component_count"] += 1
                wrong_cd = replace(path, steps=[
                    replace(path.steps[0], details=bad_details),
                    *path.steps[1:],
                ])
                self.assert_matches(original, wrong_cd, final, False)
                bad_final = replace(path, final_formula_hash="0"*64)
                self.assert_matches(original, bad_final, final, False)
                self.assertGreater(len(path.steps), 1)
                event = path.steps[1]
                forged = replace(event, assigned_literals=[99999])
                self.assert_matches(original, replace(path, steps=[
                    path.steps[0], forged, *path.steps[2:]]), final, False)
                missing = replace(event, details=dict(event.details,
                    component_id="absent"))
                self.assert_matches(original, replace(path, steps=[
                    path.steps[0], missing, *path.steps[2:]]), final, False)
                untagged = replace(event, details={
                    k: v for k, v in event.details.items()
                    if k != "component_id"
                })
                self.assert_matches(original, replace(path, steps=[
                    path.steps[0], untagged, *path.steps[2:]]), final, False)


if __name__ == "__main__":
    unittest.main()
