"""Falsification attempts for bounded weighted Walsh proof search."""

import itertools
import random
import unittest

from scripts.w034_weighted_walsh import audit_integer_weights,search_integer_certificate
from scripts.w033_walsh_bound import walsh_bound


def min_weighted_violations(nvars,clauses,weights):
    return min(sum(weight for clause,weight in zip(clauses,weights)
                   if not any(assignment[abs(lit)-1] == (lit > 0) for lit in clause))
               for assignment in itertools.product((False,True),repeat=nvars))


class TestWeightedWalsh(unittest.TestCase):
    def test_exact_integer_certificate_restores_cluttered_cube(self):
        cube = [tuple(-i if bits[i-1] else i for i in (1,2,3))
                for bits in itertools.product((False,True),repeat=3)]
        source = cube + [[4,5,6],[7,8,9]]
        self.assertEqual(walsh_bound(9,source)["status"],"NO_CERTIFICATE")
        result = search_integer_certificate(9,source)
        self.assertEqual(result["status"],"UNSAT_CERTIFIED")
        self.assertGreater(result["lower_bound_numerator"],0)
        self.assertGreater(min_weighted_violations(9,source,result["weights"]),0)

    def test_exact_checker_refuses_dangerous_underapproximation(self):
        source = [[1],[2],[-1, -2]]
        candidate = [1,0,0]
        self.assertEqual(audit_integer_weights(source,2,candidate)["status"],"NO_CERTIFICATE")
        with self.assertRaises(ValueError):
            audit_integer_weights(source,2,[-1,0,0])

    def test_sat_formula_with_clutter_cannot_be_falsely_certified(self):
        rng=random.Random(340034)
        for _ in range(30):
            target=[rng.choice((False,True)) for _ in range(4)]
            clauses=[]
            for _ in range(12):
                clause=[]
                for i in rng.sample(range(4),rng.randint(1,3)):
                    polarity=target[i] if rng.choice((True,False)) else not target[i]
                    clause.append((i+1) if polarity else -(i+1))
                if not any(target[abs(l)-1] == (l>0) for l in clause):
                    clause[0]=-clause[0]
                clauses.append(clause)
            result=search_integer_certificate(4,clauses)
            self.assertEqual(result["status"],"NO_CERTIFICATE")
            self.assertEqual(min_weighted_violations(4,clauses,result["weights"]),0)

    def test_explicit_unsat_counterexample_to_lp_completeness(self):
        # An exhaustive truth table says UNSAT, but this sufficient spectral
        # LP proof rule has no positive integer-audited certificate.
        clauses = [[1,-2,-3],[2,3,5],[1,-3,-4],[-3,4,-5],[-2,4,5],
                   [1,3,-5],[-3,-4,5],[-1,-2,-4],[-2,3,-5],[-1,4,5],
                   [1,-3,-5],[1,-3,5],[-1,2,3],[1,-2,3],
                   [1,-2,5],[2,-4,-5]]
        self.assertGreater(min_weighted_violations(5,clauses,[1]*len(clauses)),0)
        result = search_integer_certificate(5,clauses)
        self.assertEqual(result["status"],"NO_CERTIFICATE")


if __name__ == "__main__":
    unittest.main()
