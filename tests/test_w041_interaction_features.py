import itertools
import random
import unittest

from scripts.w037_geometry_features import features
from scripts.w041_interaction_features import FEATURE_NAMES,interaction_features


class W041FeatureTests(unittest.TestCase):
    def test_matches_prior_exact_features(self):
        rng=random.Random(410041)
        pool=[[s*v for s,v in zip(signs,variables)]
              for variables in itertools.combinations(range(1,9),3)
              for signs in itertools.product((-1,1),repeat=3)]
        for n in (5,8):
            candidates=[c for c in pool if max(map(abs,c))<=n]
            for size in (1,12,32):
                for _ in range(4):
                    clauses=rng.sample(candidates,size)
                    got=interaction_features(n,clauses)
                    old=features(n,clauses)
                    for key in FEATURE_NAMES[:2]:
                        self.assertAlmostEqual(got[key],old[key],places=11)

    def test_gauge_and_order_invariance(self):
        clauses=[[1,2,-3],[1,-2,4],[-1,-2,3],[2,3,-4],[-1,3,4]]
        base=interaction_features(4,clauses)
        rename={1:4,2:3,3:1,4:2}
        transformed=[[(1 if lit>0 else -1)*rename[abs(lit)]*(-1 if abs(lit) in (1,4) else 1)
                      for lit in c] for c in reversed(clauses)]
        other=interaction_features(4,transformed)
        for name in FEATURE_NAMES:
            self.assertAlmostEqual(base[name],other[name],places=11)

    def test_invalid_source_rejected(self):
        for bad in ([],[[0]],[[1,-1]],[[1,2,3,4]]):
            with self.assertRaises(ValueError):
                interaction_features(4,bad)


if __name__=='__main__':
    unittest.main()
