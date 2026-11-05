"""R-130: full native source-CNF XOR pattern discovery and diagnostics."""
import random
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.xor import canonical_xor_cnf_clauses, detect_cnf_xor_patterns


class XorDetectFullNativeRustTests(unittest.TestCase):
    def test_complete_incomplete_and_extra(self):
        for k in range(2,7):
            for rhs in (0,1):
                witness = sorted(canonical_xor_cnf_clauses(range(1,k+1),rhs))
                for clauses in (witness,witness[:-1],witness+[(1,) ]):
                    formula = CNFFormula.from_raw_clauses(clauses)
                    for include in (False,True):
                        with self.subTest(k=k,rhs=rhs,include=include,len=len(clauses)):
                            self.assertEqual(detect_cnf_xor_patterns(
                                formula,include_3var=include,backend="rust_full"),
                                detect_cnf_xor_patterns(formula,include_3var=include))

    def test_seeded_interleaved_gadgets(self):
        rng = random.Random(20261211)
        for trial in range(180):
            k = rng.randrange(2,7)
            rhs = rng.randrange(2)
            clauses = list(canonical_xor_cnf_clauses(range(1,k+1),rhs))
            for _ in range(rng.randrange(9)):
                clauses.append(tuple(sorted(rng.choice((-1,1))*v for v in
                    rng.sample(range(1,k+7),rng.randrange(1,5)))))
            formula = CNFFormula.from_raw_clauses(clauses)
            with self.subTest(trial=trial):
                self.assertEqual(detect_cnf_xor_patterns(formula,backend="rust_full"),
                                 detect_cnf_xor_patterns(formula))

    def test_max_k_disabled(self):
        formula = CNFFormula.from_raw_clauses([(1,2),(-1,-2)])
        self.assertEqual(detect_cnf_xor_patterns(formula,max_k=1,backend="rust_full"),
                         detect_cnf_xor_patterns(formula,max_k=1))


if __name__ == "__main__":
    unittest.main()
