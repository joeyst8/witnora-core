"""Exact invariance and no-target-leakage sanity checks for W037."""

import random
import unittest

from scripts.w037_geometry_features import FEATURE_NAMES,features


class TestW037(unittest.TestCase):
    def test_features_invariant_to_clause_order_and_boolean_isomorphism(self):
        rng=random.Random(370037)
        source=[]
        for _ in range(28):
            vars_=rng.sample(range(1,6),3)
            source.append([rng.choice((-1,1))*v for v in vars_])
        original=features(5,source)
        variable_mapping={1:3,2:5,3:2,4:1,5:4}
        transformed=[[(-1 if abs(lit) in (1,4) else 1)*(1 if lit>0 else -1)*variable_mapping[abs(lit)]
                      for lit in clause] for clause in reversed(source)]
        changed=features(5,transformed)
        self.assertEqual(set(original),set(FEATURE_NAMES))
        for key in FEATURE_NAMES:
            self.assertAlmostEqual(original[key],changed[key],places=10,msg=key)

    def test_no_sat_label_or_target_used(self):
        f=features(3,[[1,2,3],[-1,-2,-3]])
        self.assertEqual(set(f),set(FEATURE_NAMES))
        self.assertTrue(all(0<=value for value in f.values()))

    def test_repeated_lit_rejected(self):
        with self.assertRaises(ValueError):features(3,[[1,1,-2]])


if __name__=='__main__':
    unittest.main()
