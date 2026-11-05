"""R-031 Rust two-SAT and treewidth certificate local replay differentials."""
from __future__ import annotations

from dataclasses import replace
import os
import random
import unittest

from witnora_core.certificate import StepLogger
from witnora_core.cnf import CNFFormula
from witnora_core.primal import graph_edges, primal_graph
from witnora_core.treewidth import find_elimination_order
from witnora_core.two_sat import solve_2sat
from witnora_core.verifier_rust import replay_local_certificate_in_rust


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestNativeSolverReplay(unittest.TestCase):
    def test_1200_two_sat_sat_unsat_and_tampered_status(self):
        rng = random.Random(310112026)
        sat_count = 0
        unsat_count = 0
        for n in range(1, 9):
            for case in range(150):
                formula = CNFFormula.from_raw_clauses([
                    [rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                     for _ in range(rng.randrange(3))]
                    for _ in range(rng.randrange(12))
                ])
                logger = StepLogger()
                solution = solve_2sat(formula, logger=logger)
                step = logger.steps[0]
                ok, after, error = replay_local_certificate_in_rust(
                    formula, [step], 4, formula.formula_hash)
                with self.subTest(n=n, case=case):
                    self.assertTrue(ok, error)
                    self.assertEqual(after, formula)
                    self.assertIsNone(error)
                sat_count += solution["status"] == "SAT"
                unsat_count += solution["status"] == "UNSAT"
                wrong = replace(step, details={
                    **step.details,
                    "status": "SAT" if solution["status"] == "UNSAT" else "UNSAT",
                })
                valid, _, failure = replay_local_certificate_in_rust(
                    formula, [wrong], 4, formula.formula_hash)
                with self.subTest(n=n, case=case, tamper=True):
                    self.assertFalse(valid)
                    self.assertEqual(failure, "step 1: 2SAT_SOLVE status mismatch")
        self.assertGreater(sat_count, 0)
        self.assertGreater(unsat_count, 0)

    def test_treewidth_250_valid_and_order_tamper_rejections(self):
        rng = random.Random(310212026)
        tested = 0
        for case in range(500):
            n = rng.randrange(2, 7)
            clauses = [
                [rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                 for _ in range(rng.randrange(1, 4))]
                for _ in range(rng.randrange(10))
            ]
            formula = CNFFormula.from_raw_clauses(clauses)
            graph = primal_graph(formula)
            order = find_elimination_order(graph, 4)
            if order is None:
                continue
            logger = StepLogger()
            step = logger.append(
                "TREEWIDTH_SOLVE", formula, formula, details={
                    "elimination_order": order,
                    "primal_edges": [list(edge) for edge in graph_edges(graph)],
                })
            ok, after, error = replay_local_certificate_in_rust(
                formula, [step], 4, formula.formula_hash)
            with self.subTest(case=case):
                self.assertTrue(ok, error)
                self.assertEqual(after, formula)
            if order:
                wrong = replace(step, details={
                    **step.details, "elimination_order": list(reversed(order))[:-1],
                })
                valid, _, failure = replay_local_certificate_in_rust(
                    formula, [wrong], 4, formula.formula_hash)
                with self.subTest(case=case, tamper=True):
                    self.assertFalse(valid)
                    self.assertEqual(
                        failure, "step 1: TREEWIDTH_SOLVE order verification failed")
            tested += 1
            if tested >= 250:
                break
        self.assertEqual(tested, 250)


if __name__ == "__main__":
    unittest.main()
