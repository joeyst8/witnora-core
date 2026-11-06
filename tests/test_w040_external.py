"""Independent budgeted DPLL and SATLIB DIMACS safety tests."""

import random
import unittest

from scripts.w035_dpll_reference import solve
from scripts.w040_bounded_dpll import solve_bounded
from scripts.benchmark_w040_satlib import parse_dimacs, fixed_folds


class ExternalDPLLCases(unittest.TestCase):
    def test_uncapped_equivalence_with_reference(self):
        rng=random.Random(400040)
        pool=[[s1*a,s2*b,s3*c]
              for a in range(1,4) for b in range(a+1,5) for c in range(b+1,6)
              for s1 in (-1,1) for s2 in (-1,1) for s3 in (-1,1)]
        for m in (5,12,20):
            for _ in range(10):
                clauses=rng.sample(pool,m)
                reference=solve(clauses)
                bounded=solve_bounded(clauses,max_clause_scans=1_000_000)
                for field in ('verdict','assignment','nodes','decisions','unit_assignments','clause_scans'):
                    self.assertEqual(reference[field],bounded[field])

    def test_budget_is_exact(self):
        cases=[[[1,2,3],[-1,-2,-3]], [[1],[-1]],[[1,-2],[-1,2],[1,2]]]
        for clauses in cases:
            for cap in (1,2,3):
                bounded=solve_bounded(clauses,max_clause_scans=cap)
                self.assertLessEqual(bounded['clause_scans'],cap)
                if bounded['verdict']=='CENSORED':
                    self.assertEqual(bounded['clause_scans'],cap)

    def test_external_dimacs_strictness_and_fold_balance(self):
        source='c comment\np cnf 20 91\n' + ('1 -2 3 0\n'*91)
        parsed=parse_dimacs(source.encode('ascii'))
        self.assertEqual(len(parsed),91)
        for invalid in ('p cnf 21 91\n', 'p cnf 20 91\n1 -1 2 0\n', 'p cnf 20 91\n1 2 0\n'):
            with self.assertRaises(ValueError):
                parse_dimacs(invalid.encode('ascii'))
        folds=fixed_folds(200)
        self.assertEqual([folds.count(i) for i in range(5)],[40]*5)


if __name__=='__main__':
    unittest.main()
