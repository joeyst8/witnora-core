"""R-151/R-152: full row-trace proof candidate exact differential."""
import random
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.xor import XorEquation, canonical_xor_cnf_clauses
from witnora_core.xor_drat import _row_trace_refutation, _sparse_xor_elimination_schedule


class XorRowTraceRustTests(unittest.TestCase):
    def test_seeded_trace_and_resource_caps(self):
        rng = random.Random(151152)
        for trial in range(140):
            equations = []
            for _ in range(rng.randrange(1, 7)):
                variables = rng.sample(range(1, 7), rng.randrange(1, 4))
                rhs = rng.randrange(2)
                equations.append(XorEquation(variables, rhs,
                    source_clauses=canonical_xor_cnf_clauses(variables, rhs)))
            formula = CNFFormula([clause for eq in equations
                                   for clause in eq.source_clauses])
            trace = _sparse_xor_elimination_schedule(equations)["row_operation_trace"]
            if trial % 11 == 0 and trace:
                trace = [dict(op) for op in trace]
                trace[0]["result_rhs"] ^= 1
            if trial % 17 == 0 and trace:
                trace = [dict(op) for op in trace]
                trace[0]["left_row_id"] = "does_not_exist"
            options = dict(max_proof_clauses=rng.randrange(0, 200),
                           max_proof_bytes=rng.randrange(0, 3000),
                           timeout_seconds=None)
            with self.subTest(trial=trial):
                self.assertEqual(
                    _row_trace_refutation(formula, equations, trace,
                                          **options, backend="rust"),
                    _row_trace_refutation(formula, equations, trace, **options))

    def test_known_contradiction_and_source_rejection(self):
        equations = [
            XorEquation([1],0,source_clauses=canonical_xor_cnf_clauses([1],0)),
            XorEquation([1],1,source_clauses=canonical_xor_cnf_clauses([1],1))]
        trace = _sparse_xor_elimination_schedule(equations)["row_operation_trace"]
        full = CNFFormula([[1],[-1]])
        missing = CNFFormula([[1]])
        for formula in (full,missing):
            with self.subTest(formula=formula.num_clauses):
                self.assertEqual(_row_trace_refutation(formula,equations,trace,
                    max_proof_clauses=10,max_proof_bytes=100,
                    timeout_seconds=None,backend="rust"),
                    _row_trace_refutation(formula,equations,trace,
                    max_proof_clauses=10,max_proof_bytes=100,
                    timeout_seconds=None))


if __name__ == "__main__":
    unittest.main()
