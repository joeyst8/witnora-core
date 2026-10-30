"""Basic source identity, deterministic structural measurements."""
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.satlib_fingerprint import fingerprint


class SatlibFingerprintTests(unittest.TestCase):
    def test_legacy_eof_normalization(self):
        from scripts.benchmark_satlib_external import normalize_satlib_legacy_eof
        from witnora_core.dimacs import parse_dimacs
        source = "c fixture\\np cnf 1 1\\n1 0\\n%\\n0\\n"
        cleaned, changed = normalize_satlib_legacy_eof(source)
        self.assertTrue(changed)
        self.assertTrue(parse_dimacs(cleaned).num_clauses == 1)
        with self.assertRaises(ValueError):
            normalize_satlib_legacy_eof(source + "1 0\\n")

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
