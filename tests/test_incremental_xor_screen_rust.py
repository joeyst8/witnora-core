"""R-064: exact native/Python necessary-XOR prefilter differential tests."""
import os
import random
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.incremental_separator import (
    possible_two_xor_patterns, possible_two_xor_patterns_rust,
)
from witnora_core.xor import canonical_xor_cnf_clauses


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in Rust CI")
class IncrementalXorScreenRustTests(unittest.TestCase):
    def test_random_sources_and_exact_xor_controls(self):
        rng = random.Random(6402026)
        for case in range(800):
            nvars = rng.randrange(2, 13)
            source = [
                [rng.choice((-1, 1)) * v for v in
                 rng.sample(range(1, nvars+1), rng.randrange(1, min(nvars, 7)+1))]
                for _ in range(rng.randrange(0, 35))
            ]
            if case % 3 == 0 and nvars >= 4:
                source += [list(row) for row in canonical_xor_cnf_clauses((1,2), 1)]
                source += [list(row) for row in canonical_xor_cnf_clauses((3,4), 0)]
            formula = CNFFormula.from_raw_clauses(source)
            with self.subTest(case=case):
                self.assertEqual(possible_two_xor_patterns_rust(formula),
                                 possible_two_xor_patterns(formula))


if __name__ == "__main__":
    unittest.main()
