"""R-067: source-CNF hash and metadata parity for seeded hidden separators."""
import os
import unittest

from witnora_core.hidden_separator_challenge import (
    make_hidden_separator, make_hidden_separator_rust,
)


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in Rust CI")
class HiddenSeparatorGeneratorRustTests(unittest.TestCase):
    def test_500_seeded_source_hashes_and_metadata(self):
        for case in range(500):
            width=2+case%2
            noise=bool((case//2)%2)
            seed=6702026+case*113
            with self.subTest(case=case):
                py_formula,py_meta=make_hidden_separator(seed,width=width,
                                                          cross_noise=noise)
                rs_formula,rs_meta=make_hidden_separator_rust(seed,width=width,
                                                              cross_noise=noise)
                self.assertEqual(rs_formula.formula_hash,py_formula.formula_hash)
                self.assertEqual(rs_formula.clauses,py_formula.clauses)
                self.assertEqual(rs_meta,py_meta)
        for bad in (0,1,4,99):
            with self.assertRaises(ValueError):
                make_hidden_separator_rust(1,width=bad)


if __name__=="__main__":
    unittest.main()
