"""R-040 native fixed-separator exact XOR scaling family parity."""
from __future__ import annotations

import os
import random
import unittest

from witnora_core.cnf import formula_satisfied
from witnora_core.separator_scaling_families import (
    make_scaling_case, make_scaling_case_rust,
)


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestNativeScalingFamilies(unittest.TestCase):
    def test_all_256_bounded_source_families_exact_clause_and_metadata_parity(self):
        cases=0
        for width in (2,3):
            for blocks in range(1,129):
                reference,metadata=make_scaling_case(blocks,width)
                native,native_metadata=make_scaling_case_rust(blocks,width)
                with self.subTest(width=width,blocks=blocks):
                    self.assertEqual(native,reference)
                    self.assertEqual(native_metadata,metadata)
                    self.assertEqual(native.formula_hash,reference.formula_hash)
                    self.assertEqual(
                        native.num_clauses,2*blocks*(1<<(width+1)))
                    self.assertEqual(
                        native_metadata["expected_boundary"],
                        tuple(range(1,width+1)))
                cases+=1
        self.assertEqual(cases,256)

    def test_800_sampled_truth_assignments_match_parity_equations(self):
        rng=random.Random(401112026)
        cases=0
        for width in (2,3):
            for blocks in (1,2,3,5):
                formula,_=make_scaling_case_rust(blocks,width)
                for _ in range(100):
                    assigned={v:bool(rng.getrandbits(1)) for v in formula.variables}
                    boundary=sum(assigned[v] for v in range(1,width+1))%2
                    expected=True
                    for index in range(2*blocks):
                        a=100+2*index
                        b=a+1
                        parity=(boundary+int(assigned[a])+int(assigned[b]))%2
                        if parity!=index%2:
                            expected=False
                            break
                    self.assertEqual(formula_satisfied(formula,assigned),expected)
                    cases+=1
        self.assertEqual(cases,800)

    def test_invalid_grid_matches_python(self):
        for blocks,width in ((0,2),(129,2),(-1,2),(2,1),(2,4)):
            with self.assertRaisesRegex(ValueError,
                                        "scaling case outside bounded experiment"):
                make_scaling_case_rust(blocks,width)
            with self.assertRaisesRegex(ValueError,
                                        "scaling case outside bounded experiment"):
                make_scaling_case(blocks,width)


if __name__=="__main__":
    unittest.main()
