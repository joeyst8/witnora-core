"""R-167–R-170: native proof candidates under mixed signed source-CNF controls."""
import random
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.drat_check import check_drat_text
from witnora_core.xor import XorEquation, canonical_xor_cnf_clauses
from witnora_core.xor_drat import _row_trace_refutation, _sparse_xor_elimination_schedule


class XorMixedSourceStressRustTests(unittest.TestCase):
    def test_mixed_nonlinear_source_and_caps(self):
        rng=random.Random(167170)
        for trial in range(160):
            width=rng.randrange(1,4)
            support=rng.sample(range(1,9),width)
            equations=[XorEquation(support,rhs,
                source_clauses=canonical_xor_cnf_clauses(support,rhs))
                for rhs in (0,1)]
            clauses=[clause for equation in equations
                     for clause in equation.source_clauses]
            family=trial%4
            for _ in range(rng.randrange(0,12)):
                if family==0:  # R-167: disjoint nonlinear background
                    pool=list(range(20,35))
                elif family==1:  # R-168: overlapping signed background
                    pool=support+list(range(20,30))
                else:  # R-169: source mutation through duplicates/reordering
                    pool=list(range(1,12))+list(range(20,25))
                variables=rng.sample(pool,rng.randrange(1,min(len(pool),4)+1))
                clauses.append([v if rng.randrange(2) else -v for v in variables])
            if family==2:
                clauses.extend(clauses[:rng.randrange(0,len(clauses)+1)])
                rng.shuffle(clauses)
            formula=CNFFormula(clauses)
            trace=_sparse_xor_elimination_schedule(equations)["row_operation_trace"]
            if family==3:  # R-170: adversarial resource caps
                clause_cap=rng.choice([0,1,2,5,30,2000])
                byte_cap=rng.choice([0,2,10,20,500,40000])
            else:
                clause_cap,byte_cap=2000,40000
            options=dict(max_proof_clauses=clause_cap,
                         max_proof_bytes=byte_cap,timeout_seconds=None)
            with self.subTest(trial=trial,family=family):
                rust=_row_trace_refutation(formula,equations,trace,
                                           backend="rust",**options)
                python=_row_trace_refutation(formula,equations,trace,**options)
                self.assertEqual(rust,python)
                if rust[0] is not None:
                    self.assertIsNone(rust[1])
                    self.assertTrue(check_drat_text(formula,rust[0])["verified"])


if __name__ == "__main__":
    unittest.main()
