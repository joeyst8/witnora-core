"""R-037 native SCC implication witnesses and derived resolution units."""
from __future__ import annotations

import os
import random
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.two_sat_proof import (
    build_2sat_scc_proof, build_2sat_scc_proof_rust,
)


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestNativeTwoSatResolutionWitness(unittest.TestCase):
    def test_1600_seeded_unsat_source_paths_and_units(self):
        rng = random.Random(371112026)
        count = 0
        for n in range(1, 9):
            for _ in range(200):
                source = [[1], [-1]]
                for _ in range(rng.randrange(12)):
                    source.append([
                        rng.choice((-1, 1)) * rng.randrange(1, n+1)
                        for _ in range(rng.randrange(1, 3))
                    ])
                rng.shuffle(source)
                formula = CNFFormula.from_raw_clauses(source)
                expected = build_2sat_scc_proof(formula)
                native = build_2sat_scc_proof_rust(formula)
                with self.subTest(n=n, source=source):
                    self.assertEqual(native.to_dict(), expected.to_dict())
                    self.assertEqual(
                        native.derived_clauses[-1],
                        (native.variable,))
                    self.assertIn((-native.variable,),
                                  native.derived_clauses)
                    self.assertEqual(
                        build_2sat_scc_proof_rust(
                            formula, native.variable).to_dict(),
                        build_2sat_scc_proof(
                            formula, native.variable).to_dict())
                count += 1
        self.assertEqual(count, 1600)

    def test_sat_and_overwidth_failure_messages(self):
        for clauses in (
            [[1, 2], [-1, 2]],
            [[2, -3], [3, 4]],
            [],
        ):
            formula = CNFFormula.from_raw_clauses(clauses)
            with self.subTest(source=clauses):
                with self.assertRaisesRegex(
                    ValueError, "no mutually reachable variable"
                ):
                    build_2sat_scc_proof_rust(formula)
                with self.assertRaisesRegex(
                    ValueError, "no mutually reachable variable"
                ):
                    build_2sat_scc_proof(formula)
        with self.assertRaisesRegex(
            ValueError, "requires clauses of width"
        ):
            build_2sat_scc_proof_rust(
                CNFFormula.from_raw_clauses([[1, 2, 3]]))

    def test_real_multistep_contradiction(self):
        formula = CNFFormula.from_raw_clauses([
            [1, 2], [-1, 2], [1, -2], [-1, -2],
        ])
        native = build_2sat_scc_proof_rust(formula)
        reference = build_2sat_scc_proof(formula)
        self.assertEqual(native.to_dict(), reference.to_dict())
        self.assertGreater(len(native.path_pos_to_neg), 1)


if __name__ == "__main__":
    unittest.main()
