"""R-175–R-178: final bounded fail-closed XOR proof adversarial controls."""
import random
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.drat_check import check_drat_text
from witnora_core.xor import XorEquation, canonical_xor_cnf_clauses
from witnora_core.xor_drat import _row_trace_refutation, _sparse_xor_elimination_schedule


class XorFinalAdversarialRustTests(unittest.TestCase):
    @staticmethod
    def fixture(variables):
        equations=[XorEquation(variables,rhs,
            source_clauses=canonical_xor_cnf_clauses(variables,rhs))
            for rhs in (0,1)]
        formula=CNFFormula(clause for equation in equations
                           for clause in equation.source_clauses)
        trace=_sparse_xor_elimination_schedule(equations)["row_operation_trace"]
        return formula,equations,trace

    def compare(self,formula,equations,trace,clause_cap,byte_cap):
        opts=dict(max_proof_clauses=clause_cap,max_proof_bytes=byte_cap,
                  timeout_seconds=None)
        rust=_row_trace_refutation(formula,equations,trace,backend="rust",**opts)
        python=_row_trace_refutation(formula,equations,trace,**opts)
        self.assertEqual(rust,python)
        if rust[0] is not None:
            self.assertIsNone(rust[1])
            self.assertTrue(check_drat_text(formula,rust[0])["verified"])
        return rust

    def test_r175_source_relabeling(self):
        rng=random.Random(175)
        for trial in range(70):
            variables=rng.sample(range(1,64),rng.randrange(1,4))
            formula,equations,trace=self.fixture(variables)
            with self.subTest(trial=trial):
                result=self.compare(formula,equations,trace,2000,40000)
                self.assertIsNotNone(result[0])

    def test_r176_exact_clause_and_byte_budget_rejection(self):
        for width in (1,2,3):
            formula,equations,trace=self.fixture(list(range(1,width+1)))
            for clauses,bytes_ in ((0,100),(1,0),(2,2),(10,10),(2000,40000)):
                with self.subTest(width=width,clauses=clauses,bytes=bytes_):
                    result=self.compare(formula,equations,trace,clauses,bytes_)
                    self.assertTrue(result[0] is not None or result[1] in (
                        "SKIPPED_PROOF_SIZE_CAP","SKIPPED_PROOF_BYTES_CAP"))

    def test_r177_corrupt_trace_values_and_ids(self):
        formula,equations,trace=self.fixture([1,2,3])
        for patch in ({"left_row_id":"missing_source"},
                      {"result_rhs":0},
                      {"result_row_variables":[1]},
                      {"result_row_id":None}):
            altered=[dict(row) for row in trace]
            altered[0].update(patch)
            with self.subTest(patch=patch):
                proof,error,_=self.compare(formula,equations,altered,2000,40000)
                self.assertIsNone(proof)
                self.assertIsNotNone(error)

    def test_r178_missing_original_source_support(self):
        formula,equations,trace=self.fixture([1,2])
        source=list(formula.to_clause_lists())
        for missing_index in range(len(source)):
            reduced=CNFFormula(source[:missing_index]+source[missing_index+1:])
            with self.subTest(missing_index=missing_index):
                proof,error,_=self.compare(reduced,equations,trace,2000,40000)
                self.assertIsNone(proof)
                self.assertEqual(error,"DETECTED_XOR_SOURCE_CLAUSE_MISSING_FROM_ORIGINAL")


if __name__ == "__main__":
    unittest.main()
