"""R-066: independent support separator width native/Python parity."""
import os
import random
import unittest

from witnora_core.hidden_separator_challenge import (
    independent_parity_cut_width, independent_parity_cut_width_rust,
)


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in Rust CI")
class ParityCutWidthRustTests(unittest.TestCase):
    def test_random_hypergraph_supports(self):
        rng=random.Random(6602026)
        for case in range(500):
            nvars=rng.randrange(1,9)
            supports=[tuple(rng.sample(range(1,nvars+1),
                             rng.randrange(0,min(nvars,5)+1)))
                      for _ in range(rng.randrange(0,13))]
            limit=rng.randrange(0,4)
            with self.subTest(case=case):
                self.assertEqual(
                    independent_parity_cut_width_rust(supports,limit=limit),
                    independent_parity_cut_width(supports,limit=limit))

    def test_exact_controls_and_budgets(self):
        self.assertEqual(independent_parity_cut_width_rust([(1,2),(2,3)]),1)
        self.assertIsNone(independent_parity_cut_width_rust([(1,),(3,)]))
        self.assertIsNone(independent_parity_cut_width_rust([]))
        with self.assertRaises(ValueError):
            independent_parity_cut_width_rust([(1,2)],limit=5)
        with self.assertRaises(ValueError):
            independent_parity_cut_width_rust([(1,-2)])


if __name__=="__main__":
    unittest.main()
