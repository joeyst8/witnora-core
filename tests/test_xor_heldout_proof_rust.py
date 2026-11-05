"""R-163–R-166: held-out exact contradictory XOR proof controls."""
import random
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.drat_check import check_drat_text
from witnora_core.xor import XorEquation, canonical_xor_cnf_clauses
from witnora_core.xor_drat import _row_trace_refutation, _sparse_xor_elimination_schedule


class XorHeldoutProofRustTests(unittest.TestCase):
    @staticmethod
    def fixture(variables, reverse=False):
        equations=[XorEquation(variables,rhs,
                   source_clauses=canonical_xor_cnf_clauses(variables,rhs))
                   for rhs in (0,1)]
        if reverse:
            equations.reverse()
        formula=CNFFormula(clause for equation in equations
                           for clause in equation.source_clauses)
        trace=_sparse_xor_elimination_schedule(equations)["row_operation_trace"]
        return formula,equations,trace

    def test_heldout_exact_and_independent_rup(self):
        rng=random.Random(163164)
        for trial in range(120):
            variables=rng.sample(range(1,17),rng.randrange(1,4))
            formula,equations,trace=self.fixture(variables)
            options=dict(max_proof_clauses=2000,max_proof_bytes=40000,
                         timeout_seconds=None)
            with self.subTest(trial=trial):
                rust=_row_trace_refutation(formula,equations,trace,
                                           backend="rust",**options)
                python=_row_trace_refutation(formula,equations,trace,**options)
                self.assertEqual(rust,python)
                self.assertIsNone(rust[1])
                self.assertTrue(check_drat_text(formula,rust[0])["verified"])

    def test_tampering_and_permutation_controls(self):
        rng=random.Random(165166)
        for trial in range(80):
            variables=rng.sample(range(1,17),rng.randrange(1,4))
            for reverse in (False,True):
                formula,equations,trace=self.fixture(variables,reverse=reverse)
                proof,error,_stats=_row_trace_refutation(formula,equations,trace,
                    backend="rust",max_proof_clauses=2000,
                    max_proof_bytes=40000,timeout_seconds=None)
                with self.subTest(trial=trial,reverse=reverse):
                    self.assertIsNone(error)
                    self.assertTrue(check_drat_text(formula,proof)["verified"])
                    tampered="\n".join(proof.splitlines()[:-1])+"\n"
                    self.assertFalse(check_drat_text(formula,tampered)["verified"])


if __name__ == "__main__":
    unittest.main()
