import unittest

import numpy as np

from scripts.benchmark_w039_label_conditioned import (
    N, PER_CELL, SIZES, CELLS, clause_pool, clause_truth_masks, exact_truth,
    folds_for_cells, evaluate_models,
)


class W039Tests(unittest.TestCase):
    def test_exhaustive_clause_truth_mask(self):
        pool=clause_pool()
        self.assertEqual(len(pool),960)
        masks=clause_truth_masks(pool)
        self.assertEqual(exact_truth([[1,2,3]],masks),'SAT')
        # Explicit eight assignments excluding each pattern of x1,x2,x3.
        clauses=[[a*1,b*2,c*3] for a in (-1,1) for b in (-1,1) for c in (-1,1)]
        self.assertEqual(exact_truth(clauses,masks),'UNSAT')

    def test_cell_folds_are_balanced(self):
        cells=[cell for cell in CELLS for _ in range(PER_CELL)]
        folds=folds_for_cells(cells)
        self.assertEqual(len(folds),180)
        for cell in CELLS:
            self.assertEqual([sum(c==cell and k==fold for c,k in zip(cells,folds)) for fold in range(5)],[6]*5)

    def test_no_feature_leakage_when_one_feature_constant(self):
        cells=[cell for cell in CELLS for _ in range(PER_CELL)]
        folds=folds_for_cells(cells)
        y=np.array([np.log1p(1+i%7) for i in range(180)])
        x=np.zeros((180,3))
        base,enhanced=evaluate_models(x,y,cells,folds)
        self.assertTrue(np.allclose(base,enhanced,atol=1e-12))


if __name__=='__main__':
    unittest.main()
