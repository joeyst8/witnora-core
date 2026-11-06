"""Exact prefix I/O and sound local subset invariants for W036."""

import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.w036_local_gate import read_prefix,neighborhoods,unit_propagation_contradiction,bounded_dpll
from scripts.w030_smoke_cases import source_bytes


class TestW036(unittest.TestCase):
    def test_read_only_frozen_prefix_even_if_suffix_malformed(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'input.cnf'
            source=b'p cnf 2 4\n1 0\n-1 0\nBAD INVALID SUFFIX\n'
            path.write_bytes(source)
            p=read_prefix(path,2)
            self.assertEqual(p['read_clauses'],2)
            self.assertEqual(p['read_bytes'],len(b'p cnf 2 4\n1 0\n-1 0\n'))
            self.assertTrue(unit_propagation_contradiction([list(c) for c in p['clauses']]))
            with self.assertRaises(ValueError):
                read_prefix(path,3)

    def test_local_source_indices_only_and_caps(self):
        source=[(1,2,3),(-1,4),(-1,2),(3,-4),(5,),(-5,),(-2,-3)]
        prefix={'clauses':source,'variables':5}
        result=neighborhoods(prefix,3,4)
        self.assertLessEqual(len(result),3)
        for candidate in result:
            self.assertLessEqual(len(candidate['clauses']),4)
            self.assertEqual(candidate['clauses'],[list(source[i]) for i in candidate['source_indices']])
            self.assertEqual(len(set(candidate['source_indices'])),len(candidate['source_indices']))

    def test_neighborhood_does_not_infer_sat_from_unknown(self):
        self.assertFalse(unit_propagation_contradiction([[1,2,3],[-1,-2,-3]]))
        self.assertTrue(unit_propagation_contradiction([[1],[-1,2],[-2]]))

    def test_reject_bad_budgets(self):
        with self.assertRaises(ValueError): neighborhoods({'clauses':[(1,)],'variables':1},0)
        with self.assertRaises(ValueError): read_prefix('/no/such/file',0)

    def test_bounded_dpll_has_three_distinct_outcomes(self):
        unsat=[[1],[-1]]
        sat=[[1,2],[-1,2]]
        self.assertEqual(bounded_dpll(unsat)['status'],'UNSAT_CERTIFIED')
        self.assertEqual(bounded_dpll(sat)['status'],'SAT_SUBFORMULA')
        # Every nontrivial branch must refuse to infer UNSAT from no budget.
        self.assertEqual(bounded_dpll([[1,2],[3,4]],max_clause_scans=1)['status'],
                         'UNKNOWN_BUDGET')


if __name__=='__main__':
    unittest.main()
