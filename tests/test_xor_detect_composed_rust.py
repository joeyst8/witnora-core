"""R-129: source-CNF XOR detector with native exact encodings and overlap."""
import random
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.xor import canonical_xor_cnf_clauses, detect_cnf_xor_patterns


class XorDetectComposedRustTests(unittest.TestCase):
    def test_exact_and_incomplete_gadgets(self):
        for k in range(2, 7):
            for parity in (0, 1):
                complete = sorted(canonical_xor_cnf_clauses(range(1,k+1),parity))
                for clauses in (complete, complete[:-1],complete+[(1,)]):
                    formula = CNFFormula.from_raw_clauses(clauses)
                    with self.subTest(k=k,parity=parity,clauses=len(clauses)):
                        self.assertEqual(detect_cnf_xor_patterns(
                            formula,backend="rust"), detect_cnf_xor_patterns(formula))

    def test_seeded_mixed_formulas(self):
        rng = random.Random(20261210)
        for trial in range(120):
            k = rng.randrange(2, 7)
            parity = rng.randrange(2)
            clauses = list(canonical_xor_cnf_clauses(range(1,k+1),parity))
            for _ in range(rng.randrange(8)):
                clauses.append(tuple(sorted(rng.choice((-1,1))*v for v in
                    rng.sample(range(1,k+6),rng.randrange(1,4)))))
            formula = CNFFormula.from_raw_clauses(clauses)
            with self.subTest(trial=trial):
                self.assertEqual(detect_cnf_xor_patterns(
                    formula,backend="rust"),detect_cnf_xor_patterns(formula))


if __name__ == "__main__":
    unittest.main()
