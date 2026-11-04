"""R-069: seeded planted separator source hashes and witness parity."""
import os
import unittest
from itertools import product

from witnora_core.cnf import formula_satisfied
from witnora_core.hard_separator_families import (
    make_hard_separator_case,make_hard_separator_case_rust,
)


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in Rust CI")
class HardSeparatorGeneratorRustTests(unittest.TestCase):
    def test_complete_preregistered_grid_and_seeded_controls(self):
        for blocks,core_vars,width in product((2,4,8),(18,26),(2,3)):
            for case in range(8):
                seed=6902026+case*107
                with self.subTest(blocks=blocks,core_vars=core_vars,
                                  width=width,seed=seed):
                    py,py_meta=make_hard_separator_case(blocks,core_vars,width,seed)
                    rs,rs_meta=make_hard_separator_case_rust(blocks,core_vars,width,seed)
                    self.assertEqual(rs.formula_hash,py.formula_hash)
                    self.assertEqual(rs.clauses,py.clauses)
                    self.assertEqual(rs_meta,py_meta)
                    self.assertTrue(formula_satisfied(
                        rs,{v:True for v in rs.variables}))
        with self.assertRaises(ValueError):
            make_hard_separator_case_rust(3,18,2,9)


if __name__=="__main__":
    unittest.main()
