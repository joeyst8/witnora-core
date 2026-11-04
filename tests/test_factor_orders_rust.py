"""R-038 complete factor graph elimination and independent width replay."""
from __future__ import annotations

import os
import random
import unittest

from witnora_core.factor_elimination_orders import (
    elimination_order, elimination_order_rust,
    replay_elimination_width, replay_elimination_width_rust,
)


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestFactorEliminationNative(unittest.TestCase):
    def test_1280_random_graph_orders_all_modes(self):
        rng=random.Random(381112026)
        count=0
        for nvars in range(0, 10):
            for case in range(40):
                scopes=[]
                for _ in range(rng.randrange(0,12)):
                    scopes.append(set(rng.sample(
                        range(1,nvars+1),
                        rng.randrange(0,min(nvars,5)+1))))
                nsource=rng.randrange(nvars+1)
                beam=rng.randrange(1,9)
                for mode in ("min_degree","source_first","aux_first","beam_fill"):
                    py=elimination_order(scopes,nvars,nsource=nsource,
                                         mode=mode,beam=beam)
                    rs=elimination_order_rust(scopes,nvars,nsource=nsource,
                                              mode=mode,beam=beam)
                    with self.subTest(nvars=nvars,case=case,mode=mode):
                        self.assertEqual(rs,py)
                        self.assertEqual(
                            replay_elimination_width_rust(
                                scopes,nvars,rs.order),
                            replay_elimination_width(
                                scopes,nvars,py.order))
                        self.assertEqual(
                            replay_elimination_width_rust(
                                scopes,nvars,rs.order),rs.induced_width)
                    count+=1
        self.assertEqual(count, 1600)

    def test_negative_controls_match_reference_errors(self):
        cases=(
            ([], 1, -1, "min_degree", 2, "invalid source"),
            ([], 2, 1, "does_not_exist", 2, "unknown order mode"),
            ([], 2, 1, "beam_fill", 0, "beam must be positive"),
            ([{1, 4}], 3, 1, "min_degree", 2, "factor variable outside"),
        )
        for scopes,nvars,nsource,mode,beam,message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError,message):
                    elimination_order_rust(scopes,nvars,nsource=nsource,
                                           mode=mode,beam=beam)
                with self.assertRaisesRegex(ValueError,message):
                    elimination_order(scopes,nvars,nsource=nsource,
                                      mode=mode,beam=beam)
        for bad in ((1,1,2), (2,1), (3,2,1,4)):
            with self.assertRaisesRegex(ValueError,"order must"):
                replay_elimination_width_rust([{1,2}],3,bad)


if __name__=="__main__":
    unittest.main()
