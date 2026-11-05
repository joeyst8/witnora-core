"""Test structural fingerprints against planted bridges and false patterns."""
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.xor import canonical_xor_cnf_clauses
from witnora_core.parity_separator_fingerprint import parity_separator_fingerprint


def bridge():
    clauses = set(canonical_xor_cnf_clauses((1, 2, 3), 0))
    clauses.update(canonical_xor_cnf_clauses((3, 4, 5), 1))
    return CNFFormula.from_raw_clauses(clauses)


class ParitySeparatorFingerprintTests(unittest.TestCase):
    def test_planted_bridge_detected(self):
        f = bridge()
        result = parity_separator_fingerprint(f)
        self.assertEqual(result["exact_parity_equations"], 2)
        self.assertEqual([x["variable"] for x in result["separator_candidates"]], [3])
        self.assertFalse(result["cnf_transformed"])
        self.assertFalse(result["promoted"])

    def test_incomplete_encoding_not_mistaken_for_exact_xor(self):
        f = bridge()
        reduced = CNFFormula(f.clauses[:-1])
        result = parity_separator_fingerprint(reduced)
        self.assertLess(result["exact_parity_equations"], 2)
        self.assertEqual(result["candidate_count"], 0)

    def test_original_cnf_not_modified(self):
        f = bridge()
        original = f.formula_hash
        self.assertEqual(parity_separator_fingerprint(f), parity_separator_fingerprint(f))
        self.assertEqual(f.formula_hash, original)
        with self.assertRaises(ValueError):
            parity_separator_fingerprint(f, max_k=8)


if __name__ == "__main__":
    unittest.main()
