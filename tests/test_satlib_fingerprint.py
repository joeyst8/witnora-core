"""Basic source identity, deterministic structural measurements."""
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.satlib_fingerprint import fingerprint


class SatlibFingerprintTests(unittest.TestCase):
    def test_observational_only(self):
        source = CNFFormula.from_raw_clauses([[1, 2, 3], [-1, 2], [-2, 4]])
        first = fingerprint(source)
        self.assertEqual(first, fingerprint(source))
        self.assertEqual(first["variables"], 4)
        self.assertEqual(first["ternary_clauses"], 1)
        self.assertEqual(first["primal_components"], 1)
        self.assertEqual(first["source_sha256"], source.formula_hash)
        self.assertFalse(first["promoted"])

    def test_disconnected(self):
        source = CNFFormula.from_raw_clauses([[1, 2], [3, 4]])
        self.assertEqual(fingerprint(source)["primal_components"], 2)


if __name__ == "__main__":
    unittest.main()
