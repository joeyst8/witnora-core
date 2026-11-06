"""Independent truth table cross-check for transparent DPLL baseline."""

import itertools
import random
import unittest

from scripts.w035_dpll_reference import solve


def brute(variables,clauses):
    for bits in itertools.product((False,True),repeat=variables):
        if all(any(bits[abs(lit)-1] == (lit > 0) for lit in clause) for clause in clauses):
            return True
    return False


class TestDpll(unittest.TestCase):
    def test_known_conflicts_and_empty(self):
        for clauses,verdict in (([],"SAT"),([[]],"UNSAT"),([[1],[-1]],"UNSAT"),
                                ([[1,2],[-1,2]],"SAT")):
            self.assertEqual(solve(clauses)["verdict"],verdict)

    def test_random_1000_truth_tables(self):
        rng=random.Random(350035)
        for n in (1,2,3,4,5):
            for _ in range(200):
                clauses=[[rng.choice((-1,1))*rng.randint(1,n)
                          for _ in range(rng.randint(0,3))]
                         for _ in range(rng.randint(0,15))]
                result=solve(clauses)
                self.assertEqual(result["verdict"],"SAT" if brute(n,clauses) else "UNSAT")
                self.assertGreater(result["clause_scans"],0) if clauses else None


if __name__=="__main__":
    unittest.main()
