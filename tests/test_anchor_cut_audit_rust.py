"""R-065: source-bound cut reachability differential checks."""
import os
import random
import unittest
from itertools import combinations

from witnora_core.cnf import CNFFormula
from witnora_core.hidden_separator_challenge import (
    full_cnf_anchors_separated, full_cnf_anchors_separated_rust,
)


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in Rust CI")
class AnchorCutAuditRustTests(unittest.TestCase):
    def test_exhaustive_small_graphs_as_binary_clauses(self):
        for n in range(1, 5):
            edges = list(combinations(range(1, n+1), 2))
            for mask in range(1 << len(edges)):
                formula = CNFFormula.from_raw_clauses(
                    [edge for j, edge in enumerate(edges) if mask & (1 << j)]
                )
                for left in range(1, n+1):
                    for right in range(1, n+1):
                        for cut in ((), (left,), (right,), tuple(range(1,n+1))):
                            self.assertEqual(
                                full_cnf_anchors_separated_rust(formula, cut, left, right),
                                full_cnf_anchors_separated(formula, cut, left, right)
                            )

    def test_random_signed_source_and_cuts(self):
        rng = random.Random(6502026)
        for case in range(700):
            nvars = rng.randrange(2, 20)
            source = [
                [rng.choice((-1,1))*v for v in
                 rng.sample(range(1,nvars+1),rng.randrange(1,min(5,nvars)+1))]
                for _ in range(rng.randrange(0, 35))
            ]
            formula = CNFFormula.from_raw_clauses(source)
            cut = tuple(rng.sample(range(1,nvars+1),rng.randrange(0,min(nvars,5)+1)))
            left, right = rng.choices(range(1,nvars+2),k=2)
            with self.subTest(case=case):
                self.assertEqual(
                    full_cnf_anchors_separated_rust(formula,cut,left,right),
                    full_cnf_anchors_separated(formula,cut,left,right)
                )


if __name__ == "__main__":
    unittest.main()
